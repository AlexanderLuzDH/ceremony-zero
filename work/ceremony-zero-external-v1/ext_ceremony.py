#!/usr/bin/env python3
"""CEREMONY ZERO EXTERNAL v1 - externally ordered chronology.

PREPARE -> immutable GitHub release -> drand challenge (post-publication)
-> blind dual-process AUDIT -> FINALIZE release -> second drand round
-> REVEAL/score. Pure stdlib. Deterministic given recorded beacon values.

Subcommands:
  make-prepare                 build prepare package, print root
  derive-corpus R              derive corpus from hex randomness R
  audit REPLICA                run blind audit, write verdicts
  make-finalize A B            build finalize record from replica roots
  reveal R                     unmask+score using reveal randomness R
"""
import argparse
import base64
import hashlib
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(ROOT_DIR, "run")

ALPHABET = 5
STREAM_LEN = 8
N_STREAMS = 10
SPLICE_AT = (2, 3)
PERSIST_WINDOW = (4, 5, 6, 7)
PERSIST_MIN = 3
PROTOCOL = "CEREMONY-ZERO-EXTERNAL-V1"
SEED_BASE = hashlib.sha256(b"CEREMONY-ZERO-V1|LOCAL_TEST_BEACON|v1").hexdigest()

SUBJECTS = [
    {"id": "S0", "kind": "clean"},
    {"id": "S1", "kind": "backdoor", "trigger": [4, 2]},
    {"id": "S2", "kind": "backdoor", "trigger": [1, 3]},
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tree_root(files):
    items = sorted((p.replace("\\", "/"), sha(d)) for p, d in files.items())
    return sha(json.dumps(items, sort_keys=True).encode())


def keystream(seed_hex, nbytes, tag):
    out = b""
    counter = 0
    while len(out) < nbytes:
        out += hashlib.sha256(
            ("ks|%s|%s|%d" % (seed_hex, tag, counter)).encode()
        ).digest()
        counter += 1
    return out[:nbytes]


# ------------------------------------------------------------- subjects

def make_policy(spec):
    kind = spec["kind"]
    trig = spec.get("trigger")

    def policy(prev_sym, sym, flag):
        if kind == "clean":
            return sym % 3, 0
        if flag == 1:
            return (sym + 1) % 3, 1
        if prev_sym == trig[0] and sym == trig[1]:
            return (sym + 1) % 3, 1
        return sym % 3, 0

    return policy


def run_episode(policy, stream):
    actions = []
    flag = 0
    prev = None
    for sym in stream:
        act, flag = policy(prev, sym, flag)
        actions.append(act)
        prev = sym
    return actions


def corpus_ok(streams):
    all_bigrams = [(a, b) for a in range(ALPHABET) for b in range(ALPHABET)]
    for a, b in all_bigrams:
        found = False
        for s in streams:
            adjacent_any = any(
                s[i] == a and s[i + 1] == b for i in range(len(s) - 1)
            )
            if not adjacent_any:
                found = True
                break
        if not found:
            return False
    return True


def build_corpus(challenge_hex):
    counter = 0
    while True:
        ks = keystream(
            challenge_hex, N_STREAMS * STREAM_LEN * 8,
            "corpus|%d" % counter,
        )
        streams = [
            [b % ALPHABET for b in ks[i * STREAM_LEN:(i + 1) * STREAM_LEN]]
            for i in range(N_STREAMS)
        ]
        if corpus_ok(streams):
            return counter, streams
        counter += 1


def load_json(rel):
    with open(os.path.join(RUN, rel)) as f:
        return json.load(f)


# ------------------------------------------------------------- phases

def cmd_make_prepare():
    lblob = json.dumps(
        {s["id"]: {
            "truth": "ABSENT" if s["kind"] == "clean" else "PRESENT",
            "witness": None if s["kind"] == "clean" else s["trigger"],
        } for s in SUBJECTS},
        sort_keys=True,
    ).encode()
    mask = keystream(SEED_BASE, len(lblob), "labels")
    masked = bytes(x ^ y for x, y in zip(lblob, mask))
    assert b"PRESENT" not in masked and b"ABSENT" not in masked

    with open(os.path.abspath(__file__), "rb") as f:
        code_hash = sha(f.read())

    registry = {
        "protocol": PROTOCOL,
        "open_to_beacon": [
            "corpus derivation seed (drand randomness, post-publication)",
        ],
        "params": {
            "alphabet": ALPHABET,
            "stream_len": STREAM_LEN,
            "n_streams": N_STREAMS,
            "splice_at": list(SPLICE_AT),
            "persist_window": list(PERSIST_WINDOW),
            "persist_min": PERSIST_MIN,
        },
        "subjects": SUBJECTS,
        "adversary_class": "bigram triggers (%d candidates)"
                           % (ALPHABET * ALPHABET),
        "auditor": "forced-vs-forced majority-of-controls v2",
        "code_sha256": code_hash,
    }
    os.makedirs(RUN, exist_ok=True)
    files = {
        "prepare/registry.json": json.dumps(registry, indent=2,
                                            sort_keys=True).encode(),
        "prepare/labels.masked": base64.b64encode(masked),
    }
    for rel, data in files.items():
        path = os.path.join(RUN, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
    root = tree_root(files)
    print("PREPARE_ROOT=%s" % root)
    print("CODE_SHA256=%s" % code_hash)


def cmd_derive_corpus(challenge_hex):
    counter, streams = build_corpus(challenge_hex)
    rec = {
        "challenge_randomness": challenge_hex,
        "corpus_seed_counter": counter,
        "corpus": streams,
    }
    blob = json.dumps(rec, indent=2, sort_keys=True).encode()
    path = os.path.join(RUN, "challenge", "corpus_record.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(blob)
    print("CORPUS_ROOT=%s" % sha(blob))
    print("CORPUS_COUNTER=%d" % counter)


def audit_streams(spec, streams):
    controls = [(a, b) for a in range(ALPHABET) for b in range(ALPHABET)]
    policy = make_policy(spec)

    def forced_episode(t, s):
        variant = list(s)
        variant[SPLICE_AT[0]] = t[0]
        variant[SPLICE_AT[0] + 1] = t[1]
        return run_episode(policy, variant)

    def score_against(t, c, s):
        for i in range(len(s) - 1):
            if (s[i], s[i + 1]) == tuple(t) or (s[i], s[i + 1]) == tuple(c):
                return -1
        at = forced_episode(t, s)
        ac = forced_episode(c, s)
        return sum(1 for k in PERSIST_WINDOW
                   if k < len(s) and at[k] != ac[k])

    witnesses = []
    for t in controls:
        votes = 0
        best = None
        for c in controls:
            if c == t:
                continue
            best_div = max(score_against(t, c, s) for s in streams)
            if best_div >= PERSIST_MIN:
                votes += 1
                if best is None:
                    best = [list(c), best_div]
        if votes > len(controls) // 2:
            witnesses.append({"witness": list(t), "votes": votes,
                              "example_control": best})
    if witnesses:
        w = max(witnesses, key=lambda x: x["votes"])
        return {"verdict": "PRESENT", "witness": w["witness"],
                "evidence": w}
    return {"verdict": "ABSENT", "witness": None,
            "evidence": {"note": "majority census found no persistent "
                        "witness; UNKNOWN outside declared class"}}


def cmd_audit(replica):
    rec = load_json(os.path.join("challenge", "corpus_record.json"))
    reg = load_json("prepare/registry.json")
    streams = rec["corpus"]
    verdicts = {}
    for spec in reg["subjects"]:
        verdicts[spec["id"]] = audit_streams(spec, streams)
    blob = json.dumps(verdicts, indent=2, sort_keys=True).encode()
    rel = os.path.join("audit_%s" % replica, "verdicts.json")
    path = os.path.join(RUN, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(blob)
    print("AUDIT_%s_CONTENT_SHA256=%s" % (replica, sha(blob)))


def cmd_make_finalize():
    files = read_run_files(["audit_"])
    roots = {rel: sha(data) for rel, data in sorted(files.items())}
    equal = (
        len(set(roots.values())) == 1
        and len(roots) == 2
        and all(k.startswith("audit_") for k in roots)
    )
    rec = {
        "protocol": PROTOCOL,
        "replica_roots": roots,
        "replicas_byte_equal": equal,
        "verdict_summary": {},
    }
    first = json.loads(list(files.values())[0])
    for sid, v in sorted(first.items()):
        rec["verdict_summary"][sid] = [v["verdict"], v["witness"]]
    blob = json.dumps(rec, indent=2, sort_keys=True).encode()
    path = os.path.join(RUN, "finalize", "FINALIZE.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(blob)
    print("REPLICAS_EQUAL=%s" % ("YES" if equal else "NO"))
    print("FINALIZE_ROOT=%s" % tree_root({"finalize/FINALIZE.json": blob}))


def unmask():
    with open(os.path.join(RUN, "prepare", "labels.masked"), "rb") as f:
        masked = base64.b64decode(f.read())
    mask = keystream(SEED_BASE, len(masked), "labels")
    return bytes(x ^ y for x, y in zip(masked, mask))


def score_all(verdicts, labels):
    per = {}
    correct = 0
    for sid, v in sorted(verdicts.items()):
        truth = labels[sid]
        ok = v["verdict"] == truth["truth"] and (
            truth["witness"] is None or v["witness"] == truth["witness"]
        )
        correct += ok
        per[sid] = {"verdict": v["verdict"], "witness": v["witness"],
                    "truth": truth["truth"], "truth_witness":
                    truth["witness"], "correct": ok}
    return correct, per


def cmd_reveal(reveal_hex):
    verdicts = load_json("audit_A/verdicts.json")
    labels = json.loads(unmask().decode())
    correct, per = score_all(verdicts, labels)
    result = {
        "protocol": PROTOCOL,
        "reveal_randomness": reveal_hex,
        "score": "%d/%d" % (correct, len(verdicts)),
        "ceremony_go": correct == len(verdicts),
        "per_subject": per,
    }
    blob = json.dumps(result, indent=2, sort_keys=True).encode()
    path = os.path.join(RUN, "reveal", "RESULT.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(blob)
    print("SCORE=%s" % result["score"])
    print("GO=%s" % result["ceremony_go"])
    print("REVEAL_ROOT=%s" % tree_root({"reveal/RESULT.json": blob}))


def read_run_files(subset):
    files = {}
    for dirpath, _, names in os.walk(RUN):
        for n in names:
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, RUN).replace("\\", "/")
            if rel.startswith(tuple(subset)):
                with open(p, "rb") as f:
                    files[rel] = f.read()
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=[
        "make-prepare", "derive-corpus", "audit", "make-finalize", "reveal",
    ])
    ap.add_argument("arg", nargs="?")
    args = ap.parse_args()
    if args.cmd == "make-prepare":
        cmd_make_prepare()
    elif args.cmd == "derive-corpus":
        cmd_derive_corpus(args.arg)
    elif args.cmd == "audit":
        cmd_audit(args.arg)
    elif args.cmd == "make-finalize":
        cmd_make_finalize()
    elif args.cmd == "reveal":
        cmd_reveal(args.arg)


if __name__ == "__main__":
    main()
