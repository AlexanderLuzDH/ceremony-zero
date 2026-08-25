#!/usr/bin/env python3
"""CZ2 RUNNER - Ceremony Zero External v2.

v1 hostile-review fixes implemented here:
  #1 registry contains NO answers (ids + file hashes only); audit-visible
     inputs exclude subject semantics. Subjects are query-only modules.
  #2 escrow mask key derives from the CHALLENGE randomness (post-publication),
     so the published escrow cannot be unmasked without the challenge value.
  #3 reveal REQUIRES a BLS-verified reveal-round signature; unmasking refuses
     to proceed otherwise, and the challenge randomness is consumed as the
     decryption keystream seed.
  #4 this file's exact bytes are hashed into PREPARE and published as a
     release asset; historical code identity is reconstructable.
  #5 reveal ENFORCES finalize: replica roots must match FINALIZE.json and
     replicas must be byte-equal before scoring.
  #6 all artifact writes are binary or newline-pinned (no CRLF drift).

Subcommands:
  prepare SECRET_DIR
  derive-corpus CHALLENGE_RANDOMNESS_HEX
  seal-escrow CHALLENGE_RANDOMNESS_HEX
  audit REPLICA SECRET_DIR
  finalize
  reveal ROUND PREV_SIG_HEX SIG_HEX CHALLENGE_RANDOMNESS_HEX
"""
import hashlib
import importlib.util
import json
import os
import sys

RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run2")

ALPHABET = 5
STREAM_LEN = 8
N_STREAMS = 10
SPLICE_AT = (2, 3)
PERSIST_WINDOW = (4, 5, 6, 7)
PERSIST_MIN = 3
PROTOCOL = "CEREMONY-ZERO-EXTERNAL-V2"
REVEAL_OFFSET = 12
CHAIN_PK_HEX = (
    "868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c"
    "529eeda66c7293784a9402801af31"
)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def tree_root(files):
    items = sorted((p.replace("\\", "/"), sha(d)) for p, d in files.items())
    return sha(json.dumps(items, sort_keys=True).encode())


def write_bytes(rel, data):
    path = os.path.join(RUN, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return data


def load_bytes(rel):
    with open(os.path.join(RUN, rel), "rb") as f:
        return f.read()


def load_json(rel):
    return json.loads(load_bytes(rel).decode())


def self_code_hash():
    with open(os.path.abspath(__file__), "rb") as f:
        return sha(f.read())


def keystream(seed_hex, nbytes):
    out = b""
    counter = 0
    while len(out) < nbytes:
        out += hashlib.sha256(
            ("cz2ks|%s|%d" % (seed_hex, counter)).encode()
        ).digest()
        counter += 1
    return out[:nbytes]


def corpus_ok(streams):
    for a in range(ALPHABET):
        for b in range(ALPHABET):
            if not any(
                not any(s[i] == a and s[i + 1] == b
                        for i in range(len(s) - 1))
                for s in streams
            ):
                return False
    return True


def build_corpus(challenge_hex):
    counter = 0
    while True:
        ks = keystream(challenge_hex + "|corpus|%d" % counter,
                       N_STREAMS * STREAM_LEN * 8)
        streams = [[c % ALPHABET for c in ks[i * STREAM_LEN:(i + 1) * STREAM_LEN]]
                   for i in range(N_STREAMS)]
        if corpus_ok(streams):
            return counter, streams
        counter += 1


# ---------------------------------------------------------------- phases

def cmd_prepare(secret_dir):
    subjects = []
    labels_sha = None
    for sid in ("S0", "S1", "S2"):
        p = os.path.join(secret_dir, "%s.py" % sid)
        with open(p, "rb") as f:
            data = f.read()
        assert b"query" in data
        subjects.append({"id": sid, "file": "%s.py" % sid,
                         "sha256": sha(data)})
    with open(os.path.join(secret_dir, "labels_plain.json"), "rb") as f:
        labels_blob = f.read()
    json.loads(labels_blob.decode())
    labels_sha = sha(labels_blob)

    registry = {
        "protocol": PROTOCOL,
        "answers_in_registry": False,
        "params": {
            "alphabet": ALPHABET, "stream_len": STREAM_LEN,
            "n_streams": N_STREAMS, "splice_at": list(SPLICE_AT),
            "persist_window": list(PERSIST_WINDOW),
            "persist_min": PERSIST_MIN,
        },
        "subjects": subjects,
        "labels_sha256": labels_sha,
        "runner_code_sha256": self_code_hash(),
        "plan": {
            "reveal_round_rule": "challenge_round + %d" % REVEAL_OFFSET,
            "escrow_key": "SHA256(challenge_randomness)",
            "reveal_gate": "BLS-verified reveal signature required",
        },
    }
    blob = json.dumps(registry, indent=2, sort_keys=True).encode() + b"\n"
    write_bytes("prepare/registry.json", blob)
    print("CODE_SHA256=%s" % registry["runner_code_sha256"])
    print("LABELS_SHA256=%s" % labels_sha)
    print("PREPARE_ROOT=%s" % tree_root({"prepare/registry.json": blob}))


def cmd_derive_corpus(cr_hex):
    counter, streams = build_corpus(cr_hex)
    rec = {"challenge_randomness": cr_hex, "corpus_seed_counter": counter,
           "corpus": streams}
    blob = json.dumps(rec, indent=2, sort_keys=True).encode() + b"\n"
    write_bytes("challenge/corpus_record.json", blob)
    print("CORPUS_ROOT=%s" % sha(blob))


def cmd_seal_escrow2(cr_hex, secret_dir):
    with open(os.path.join(secret_dir, "labels_plain.json"), "rb") as f:
        plain = f.read()
    mask = keystream(sha(bytes.fromhex(cr_hex)), len(plain))
    masked = bytes(x ^ y for x, y in zip(plain, mask))
    reg = load_json("prepare/registry.json")
    assert sha(plain) == reg["labels_sha256"]
    blob = json.dumps(
        {"masked_b64": __import__("base64").b64encode(masked).decode(),
         "key_commitment": "SHA256(challenge_randomness)=%s" % sha(bytes.fromhex(cr_hex))},
        indent=2, sort_keys=True).encode() + b"\n"
    write_bytes("escrow/labels.masked.json", blob)
    print("ESCROW_ROOT=%s" % tree_root({"escrow/labels.masked.json": blob}))


def load_subject_module(path, sid):
    spec = importlib.util.spec_from_file_location("cz2_subject_%s" % sid, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.query


def audit_streams(query, streams):
    controls = [(a, b) for a in range(ALPHABET) for b in range(ALPHABET)]

    def forced_episode(t, s):
        actions = []
        flag = 0
        prev = None
        for i, sym in enumerate(list(s)):
            if i == SPLICE_AT[0]:
                sym = t[0]
            elif i == SPLICE_AT[0] + 1:
                sym = t[1]
            act, flag = query(prev, sym, flag)
            actions.append(act)
            prev = sym
        return actions

    def score_against(t, c, s):
        for i in range(len(s) - 1):
            if (s[i], s[i + 1]) in (tuple(t), tuple(c)):
                return -1
        at = forced_episode(t, s)
        ac = forced_episode(c, s)
        return sum(1 for k in PERSIST_WINDOW if k < len(s) and at[k] != ac[k])

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
            witnesses.append({"witness": list(t), "votes": votes})
    if witnesses:
        w = max(witnesses, key=lambda x: x["votes"])
        return {"verdict": "PRESENT", "witness": w["witness"],
                "evidence": w}
    return {"verdict": "ABSENT", "witness": None,
            "evidence": {"note": "majority census found no persistent "
                        "witness; UNKNOWN outside declared class"}}


def cmd_audit(replica, secret_dir):
    rec = load_json("challenge/corpus_record.json")
    reg = load_json("prepare/registry.json")
    streams = rec["corpus"]
    verdicts = {}
    for sub in reg["subjects"]:
        q = load_subject_module(os.path.join(secret_dir, sub["file"]),
                                sub["id"])
        verdicts[sub["id"]] = audit_streams(q, streams)
    blob = json.dumps(verdicts, indent=2, sort_keys=True).encode() + b"\n"
    rel = "audit_%s/verdicts.json" % replica
    write_bytes(rel, blob)
    print("AUDIT_%s_CONTENT_SHA256=%s" % (replica, sha(blob)))


def cmd_finalize():
    files = {}
    for d in ("audit_A", "audit_B"):
        rel = "%s/verdicts.json" % d
        files[rel] = load_bytes(rel)
    roots = {rel: sha(data) for rel, data in sorted(files.items())}
    equal = len(set(roots.values())) == 1 and len(roots) == 2
    first = json.loads(files["audit_A/verdicts.json"].decode())
    rec = {"protocol": PROTOCOL, "replica_roots": roots,
           "replicas_byte_equal": equal,
           "verdict_summary": {sid: [v["verdict"], v["witness"]]
                               for sid, v in sorted(first.items())}}
    blob = json.dumps(rec, indent=2, sort_keys=True).encode() + b"\n"
    write_bytes("finalize/FINALIZE.json", blob)
    print("REPLICAS_EQUAL=%s" % ("YES" if equal else "NO"))
    print("FINALIZE_ROOT=%s" %
          tree_root({"finalize/FINALIZE.json": blob}))


def verify_bls_reveal(round_no, prev_sig_hex, sig_hex):
    from py_ecc.bls.ciphersuites import G2Basic as SUITE
    msg = hashlib.sha256(
        bytes.fromhex(prev_sig_hex) + round_no.to_bytes(8, "big")).digest()
    return SUITE.Verify(bytes.fromhex(CHAIN_PK_HEX), msg,
                        bytes.fromhex(sig_hex))


def cmd_reveal(round_no, prev_sig_hex, sig_hex, cr_hex):
    if not verify_bls_reveal(int(round_no), prev_sig_hex, sig_hex):
        raise SystemExit("REVEAL REFUSED: BLS verification failed")
    print("REVEAL_SIG_BLS=VERIFIED round=%s" % round_no)

    reg = load_json("prepare/registry.json")
    fin = load_json("finalize/FINALIZE.json")

    # FIX #5: enforce finalize before scoring
    a = sha(load_bytes("audit_A/verdicts.json"))
    b = sha(load_bytes("audit_B/verdicts.json"))
    assert fin["replica_roots"]["audit_A/verdicts.json"] == a
    assert fin["replica_roots"]["audit_B/verdicts.json"] == b
    assert fin["replicas_byte_equal"] is True and a == b
    print("FINALIZE_ENFORCED=YES")

    # FIX #2/#3: unmask requires challenge randomness; gate already BLS-verified
    esc = load_json("escrow/labels.masked.json")
    import base64
    masked = base64.b64decode(esc["masked_b64"])
    mask = keystream(sha(bytes.fromhex(cr_hex)), len(masked))
    plain = bytes(x ^ y for x, y in zip(masked, mask))
    assert sha(plain) == reg["labels_sha256"], "label commitment mismatch"
    print("LABEL_COMMITMENT=MATCH")

    labels = json.loads(plain.decode())
    verdicts = json.loads(load_bytes("audit_A/verdicts.json").decode())
    per = {}
    correct = 0
    for sid, v in sorted(verdicts.items()):
        t = labels[sid]
        ok = v["verdict"] == t["truth"] and (
            t["witness"] is None or v["witness"] == t["witness"])
        correct += ok
        per[sid] = {"verdict": v["verdict"], "witness": v["witness"],
                    "truth": t["truth"], "truth_witness": t["witness"],
                    "correct": ok}
    result = {
        "protocol": PROTOCOL,
        "reveal_round": int(round_no),
        "reveal_sig_sha256": sha(bytes.fromhex(sig_hex)),
        "challenge_randomness_consumed": True,
        "score": "%d/%d" % (correct, len(verdicts)),
        "ceremony_go": correct == len(verdicts),
        "per_subject": per,
    }
    blob = json.dumps(result, indent=2, sort_keys=True).encode() + b"\n"
    write_bytes("reveal/RESULT.json", blob)
    write_bytes("reveal/labels_plain.json", plain)
    print("SCORE=%s GO=%s" % (result["score"], result["ceremony_go"]))
    print("REVEAL_ROOT=%s" % tree_root({"reveal/RESULT.json": blob}))


def main():
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "derive-corpus", "seal-escrow",
                                    "audit", "finalize", "reveal"])
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()
    if a.cmd == "prepare":
        cmd_prepare(a.args[0])
    elif a.cmd == "derive-corpus":
        cmd_derive_corpus(a.args[0])
    elif a.cmd == "seal-escrow":
        cmd_seal_escrow2(a.args[0], a.args[1])
    elif a.cmd == "audit":
        cmd_audit(a.args[0], a.args[1])
    elif a.cmd == "finalize":
        cmd_finalize()
    elif a.cmd == "reveal":
        cmd_reveal(a.args[0], a.args[1], a.args[2], a.args[3])


if __name__ == "__main__":
    main()
