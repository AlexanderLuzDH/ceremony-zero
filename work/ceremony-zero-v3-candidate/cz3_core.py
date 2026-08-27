#!/usr/bin/env python3
"""Ceremony Zero v3 authority-NONE candidate core.

The auditor is a pure exhaustive black-box classifier. The verifier is total:
malformed or substituted transcripts return ``ok: false`` instead of granting
authority or raising to the caller.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from typing import Any, Callable, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


PROTOCOL = "CEREMONY-ZERO-V3-CANDIDATE"
AUTHORITY = "AUTHORITY_NONE_PRE_CUSTODY"
ALPHABET = 5
SOURCE_FILES = ("CHARTER.md", "PROTOCOL.md", "cz3_core.py", "make_test_fixture.py")
COMMITMENT_SCHEME = "SHA256_DOMAIN_CANONICAL_RUN_ID_NONCE256_VALUE_V1"
ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class Refusal(ValueError):
    """A deterministic protocol refusal."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def domain_hash(domain: str, value: Any) -> str:
    return sha256_hex(domain.encode("ascii") + b"\x00" + canonical_json(value))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Refusal(message)


def require_exact_keys(value: Any, keys: set[str], name: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{name} must be an object")
    require(set(value) == keys, f"{name} keys do not match schema")
    return value


def require_hex(value: Any, nbytes: int, name: str) -> str:
    require(isinstance(value, str), f"{name} must be hex text")
    require(len(value) == nbytes * 2, f"{name} must encode {nbytes} bytes")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise Refusal(f"{name} is not hexadecimal") from exc
    return value.lower()


def require_id(value: Any, name: str = "subject id") -> str:
    require(isinstance(value, str) and ID_PATTERN.fullmatch(value) is not None,
            f"{name} is not opaque-id syntax")
    return value


def record_root(record: Mapping[str, Any]) -> str:
    return domain_hash("CZ3-RECORD-v1", record)


def payload_hash(payload: Mapping[str, Any]) -> str:
    return domain_hash("CZ3-PAYLOAD-v1", payload)


def key_id(public_key_hex: str) -> str:
    return sha256_hex(bytes.fromhex(require_hex(public_key_hex, 32, "public key")))


def public_key_hex(private_key: Ed25519PrivateKey) -> str:
    public = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return public.hex()


def sign_record(payload: Mapping[str, Any], private_key: Ed25519PrivateKey) -> dict[str, Any]:
    digest = payload_hash(payload)
    public_hex = public_key_hex(private_key)
    return {
        "payload": dict(payload),
        "payload_sha256": digest,
        "signature": private_key.sign(bytes.fromhex(digest)).hex(),
        "signer_key_id": key_id(public_hex),
    }


def verify_signed_record(record: Any, expected_public_key_hex: str, name: str) -> dict[str, Any]:
    item = require_exact_keys(
        record,
        {"payload", "payload_sha256", "signature", "signer_key_id"},
        name,
    )
    expected_public_key_hex = require_hex(
        expected_public_key_hex, 32, "expected public key"
    )
    digest = payload_hash(item["payload"])
    require(item["payload_sha256"] == digest, f"{name} payload hash mismatch")
    require(item["signer_key_id"] == key_id(expected_public_key_hex),
            f"{name} signer key mismatch")
    signature_hex = require_hex(item["signature"], 64, f"{name} signature")
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(expected_public_key_hex)).verify(
            bytes.fromhex(signature_hex), bytes.fromhex(digest)
        )
    except Exception as exc:
        raise Refusal(f"{name} signature invalid") from exc
    require(isinstance(item["payload"], dict), f"{name} payload must be an object")
    return item["payload"]


def source_manifest(source_dir: pathlib.Path | str) -> dict[str, str]:
    base = pathlib.Path(source_dir)
    manifest: dict[str, str] = {}
    for rel in SOURCE_FILES:
        path = base / rel
        require(path.is_file(), f"source file missing: {rel}")
        manifest[rel] = sha256_hex(path.read_bytes())
    return manifest


def source_root(manifest: Mapping[str, str]) -> str:
    return domain_hash("CZ3-SOURCE-v1", dict(manifest))


def trust_anchor_root(anchor: Mapping[str, Any]) -> str:
    return domain_hash("CZ3-TRUST-ANCHOR-v1", anchor)


def validate_anchor(anchor: Any, actual_manifest: Mapping[str, str]) -> dict[str, Any]:
    item = require_exact_keys(
        anchor,
        {
            "authority",
            "candidate_source_root",
            "custodian_id",
            "ed25519_public_key",
            "kind",
            "run_mode",
            "source_manifest",
        },
        "trust anchor",
    )
    require(item["kind"] == "CEREMONY_ZERO_V3_EXTERNAL_TRUST_ANCHOR",
            "trust anchor kind mismatch")
    require(item["authority"] == AUTHORITY, "trust anchor authority mismatch")
    require(isinstance(item["custodian_id"], str) and item["custodian_id"],
            "custodian id missing")
    require(isinstance(item["run_mode"], str) and item["run_mode"],
            "run mode missing")
    require_hex(item["ed25519_public_key"], 32, "trust anchor public key")
    require(item["source_manifest"] == dict(actual_manifest),
            "trust anchor source manifest mismatch")
    require(item["candidate_source_root"] == source_root(actual_manifest),
            "trust anchor source root mismatch")
    return item


def validate_subject_spec(value: Any) -> dict[str, Any]:
    item = require_exact_keys(value, {"id", "kind", "trigger"}, "subject spec")
    require_id(item["id"])
    require(item["kind"] in {"CLEAN", "BIGRAM_PERSISTENT"},
            "subject kind outside declared class")
    if item["kind"] == "CLEAN":
        require(item["trigger"] is None, "clean subject must have null trigger")
    else:
        trigger = item["trigger"]
        require(isinstance(trigger, list) and len(trigger) == 2,
                "trigger must be a two-symbol list")
        require(all(type(x) is int and 0 <= x < ALPHABET for x in trigger),
                "trigger symbol outside alphabet")
    return item


def expected_label(spec: Mapping[str, Any]) -> dict[str, Any]:
    if spec["kind"] == "CLEAN":
        return {"truth": "ABSENT", "witness": None}
    return {"truth": "PRESENT", "witness": list(spec["trigger"])}


def validate_population(subjects: Any, labels: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require(isinstance(subjects, list) and len(subjects) == 26,
            "population must contain exactly 26 subjects")
    checked = [validate_subject_spec(x) for x in subjects]
    ids = [x["id"] for x in checked]
    require(len(set(ids)) == 26, "subject ids must be unique")
    clean_count = sum(x["kind"] == "CLEAN" for x in checked)
    triggers = {
        tuple(x["trigger"])
        for x in checked
        if x["kind"] == "BIGRAM_PERSISTENT"
    }
    expected_triggers = {(a, b) for a in range(ALPHABET) for b in range(ALPHABET)}
    require(clean_count == 1, "population must contain one clean subject")
    require(triggers == expected_triggers and len(triggers) == 25,
            "population must contain each bigram trigger exactly once")
    require(isinstance(labels, dict) and set(labels) == set(ids),
            "labels must cover the exact opaque ids")
    for spec in checked:
        label = require_exact_keys(labels[spec["id"]], {"truth", "witness"},
                                   "ground-truth label")
        require(label == expected_label(spec), "label does not match revealed subject")
    return checked, labels


def commitment(domain: str, run_id: str, nonce_hex: str, value: Any) -> str:
    require(isinstance(run_id, str) and run_id, "run id missing")
    nonce_hex = require_hex(nonce_hex, 32, f"{domain} nonce")
    return domain_hash(domain, {"nonce": nonce_hex, "run_id": run_id, "value": value})


def subject_commitment(run_id: str, nonce_hex: str, subjects: Any) -> str:
    require(isinstance(subjects, list), "subjects must be a list")
    ordered = sorted(subjects, key=lambda x: x.get("id", "") if isinstance(x, dict) else "")
    return commitment("CZ3-SUBJECT-COMMITMENT-v1", run_id, nonce_hex, ordered)


def labels_commitment(run_id: str, nonce_hex: str, labels: Any) -> str:
    require(isinstance(labels, dict), "labels must be an object")
    return commitment("CZ3-LABEL-COMMITMENT-v1", run_id, nonce_hex, labels)


def query_domain() -> list[list[int | None]]:
    return [
        [prev, sym, flag]
        for prev in [None, *range(ALPHABET)]
        for sym in range(ALPHABET)
        for flag in (0, 1)
    ]


def query_domain_root() -> str:
    return domain_hash("CZ3-QUERY-DOMAIN-v1", query_domain())


def query_spec(spec: Mapping[str, Any], prev: int | None, sym: int, flag: int) -> list[int]:
    require(prev is None or (type(prev) is int and 0 <= prev < ALPHABET),
            "previous symbol outside domain")
    require(type(sym) is int and 0 <= sym < ALPHABET, "symbol outside domain")
    require(type(flag) is int and flag in (0, 1), "flag outside domain")
    if spec["kind"] == "CLEAN":
        return [sym % 3, 0]
    triggered = flag == 1 or [prev, sym] == list(spec["trigger"])
    return [(sym + 1) % 3, 1] if triggered else [sym % 3, 0]


def reference_specs() -> list[dict[str, Any]]:
    refs = [{"id": "REFERENCE", "kind": "CLEAN", "trigger": None}]
    refs.extend(
        {"id": "REFERENCE", "kind": "BIGRAM_PERSISTENT", "trigger": [a, b]}
        for a in range(ALPHABET)
        for b in range(ALPHABET)
    )
    return refs


def response_table_for_spec(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {"input": triple, "output": query_spec(spec, triple[0], triple[1], triple[2])}
        for triple in query_domain()
    ]


def classify_responses(responses: Any) -> dict[str, Any]:
    if not isinstance(responses, list) or len(responses) != len(query_domain()):
        return {"reason": "INCOMPLETE_QUERY_DOMAIN", "verdict": "UNKNOWN", "witness": None}
    observed_outputs: list[Any] = []
    for expected_input, row in zip(query_domain(), responses):
        if not isinstance(row, dict) or row.get("input") != expected_input:
            return {"reason": "QUERY_ORDER_OR_DOMAIN_MISMATCH", "verdict": "UNKNOWN", "witness": None}
        if set(row) != {"input", "output"}:
            return {"reason": "ORACLE_QUERY_FAILED", "verdict": "UNKNOWN", "witness": None}
        output = row["output"]
        if not (
            isinstance(output, list)
            and len(output) == 2
            and type(output[0]) is int
            and 0 <= output[0] < 3
            and type(output[1]) is int
            and output[1] in (0, 1)
        ):
            return {"reason": "INVALID_ORACLE_OUTPUT", "verdict": "UNKNOWN", "witness": None}
        observed_outputs.append(output)

    matches = []
    for ref in reference_specs():
        expected = [row["output"] for row in response_table_for_spec(ref)]
        if observed_outputs == expected:
            matches.append(ref)
    if len(matches) != 1:
        reason = "NO_FINITE_CLASS_MATCH" if not matches else "AMBIGUOUS_FINITE_CLASS_MATCH"
        return {"reason": reason, "verdict": "UNKNOWN", "witness": None}
    return {
        "reason": "UNIQUE_FINITE_CLASS_MATCH",
        "verdict": expected_label(matches[0])["truth"],
        "witness": expected_label(matches[0])["witness"],
    }


def audit_oracles(oracles: Mapping[str, Callable[[int | None, int, int], Any]]) -> dict[str, Any]:
    require(isinstance(oracles, Mapping) and len(oracles) == 26,
            "auditor requires exactly 26 opaque oracles")
    rows = []
    for subject_id in sorted(oracles):
        require_id(subject_id)
        oracle = oracles[subject_id]
        require(callable(oracle), "oracle must be callable")
        responses = []
        for triple in query_domain():
            try:
                output = oracle(triple[0], triple[1], triple[2])
                if not isinstance(output, list):
                    output = list(output) if isinstance(output, tuple) else output
                row = {"input": triple, "output": output}
            except Exception:
                row = {"error": "ORACLE_QUERY_FAILED", "input": triple}
            responses.append(row)
        classification = classify_responses(responses)
        rows.append({"id": subject_id, "responses": responses, **classification})
    return {
        "query_domain_root": query_domain_root(),
        "subjects": rows,
    }


def audit_from_specs(subjects: list[dict[str, Any]]) -> dict[str, Any]:
    oracles = {
        spec["id"]: (
            lambda prev, sym, flag, held=spec: query_spec(held, prev, sym, flag)
        )
        for spec in subjects
    }
    return audit_oracles(oracles)


def validate_audit(audit: Any, subject_ids: list[str]) -> dict[str, Any]:
    item = require_exact_keys(audit, {"query_domain_root", "subjects"}, "audit")
    require(item["query_domain_root"] == query_domain_root(),
            "audit query-domain root mismatch")
    require(isinstance(item["subjects"], list) and len(item["subjects"]) == 26,
            "audit must contain exactly 26 subject transcripts")
    require([row.get("id") for row in item["subjects"]] == sorted(subject_ids),
            "audit opaque ids mismatch or reorder")
    for row in item["subjects"]:
        require_exact_keys(
            row, {"id", "reason", "responses", "verdict", "witness"},
            "audit subject",
        )
        require_id(row["id"])
        expected = classify_responses(row["responses"])
        require(row["verdict"] == expected["verdict"], "audit verdict mismatch")
        require(row["witness"] == expected["witness"], "audit witness mismatch")
        require(row["reason"] == expected["reason"], "audit reason mismatch")
    return item


def has_secret_field(value: Any) -> bool:
    forbidden = {"label_nonce", "labels", "opening", "subject_nonce", "truth"}
    if isinstance(value, dict):
        return bool(set(value) & forbidden) or any(has_secret_field(x) for x in value.values())
    if isinstance(value, list):
        return any(has_secret_field(x) for x in value)
    return False


COMMON_KEYS = {"authority", "phase", "prior_root", "protocol", "run_id", "run_mode", "sequence", "source_root", "trust_anchor_root"}


def verify_transcript(
    anchor: Any,
    prepare_record: Any,
    finalize_record: Any,
    reveal_record: Any,
    externally_pinned_prepare_root: Any,
    externally_pinned_finalize_root: Any,
    source_dir: pathlib.Path | str,
) -> dict[str, Any]:
    """Return a deterministic verification result; never raise to the caller."""
    try:
        manifest = source_manifest(source_dir)
        checked_anchor = validate_anchor(anchor, manifest)
        anchor_root = trust_anchor_root(checked_anchor)
        public_key = checked_anchor["ed25519_public_key"]
        expected_prepare = require_hex(
            externally_pinned_prepare_root, 32, "externally pinned PREPARE root"
        )
        expected_finalize = require_hex(
            externally_pinned_finalize_root, 32, "externally pinned FINALIZE root"
        )

        prepare = verify_signed_record(prepare_record, public_key, "PREPARE record")
        finalize = verify_signed_record(finalize_record, public_key, "FINALIZE record")
        reveal = verify_signed_record(reveal_record, public_key, "REVEAL record")
        actual_prepare = record_root(prepare_record)
        actual_finalize = record_root(finalize_record)
        actual_reveal = record_root(reveal_record)
        require(actual_prepare == expected_prepare, "PREPARE root not externally pinned")
        require(actual_finalize == expected_finalize, "FINALIZE root not externally pinned")

        prepare_keys = COMMON_KEYS | {
            "commitment_scheme", "labels_commitment", "query_domain_root",
            "source_manifest", "subject_commitment", "subject_ids",
        }
        require_exact_keys(prepare, prepare_keys, "PREPARE payload")
        require(not has_secret_field(prepare), "PREPARE discloses a secret field")
        require(prepare["phase"] == "PREPARE" and prepare["sequence"] == 0,
                "PREPARE phase or sequence mismatch")
        require(prepare["prior_root"] is None, "PREPARE prior root must be null")
        require(prepare["protocol"] == PROTOCOL and prepare["authority"] == AUTHORITY,
                "PREPARE protocol or authority mismatch")
        require(prepare["run_mode"] == checked_anchor["run_mode"],
                "PREPARE run mode mismatch")
        require(prepare["trust_anchor_root"] == anchor_root,
                "PREPARE trust-anchor root mismatch")
        require(prepare["source_manifest"] == manifest,
                "PREPARE source manifest mismatch")
        require(prepare["source_root"] == source_root(manifest),
                "PREPARE source root mismatch")
        require(prepare["query_domain_root"] == query_domain_root(),
                "PREPARE query-domain root mismatch")
        require(prepare["commitment_scheme"] == COMMITMENT_SCHEME,
                "PREPARE commitment scheme mismatch")
        require_hex(prepare["subject_commitment"], 32, "subject commitment")
        require_hex(prepare["labels_commitment"], 32, "labels commitment")
        require(isinstance(prepare["subject_ids"], list) and len(prepare["subject_ids"]) == 26,
                "PREPARE must bind 26 opaque ids")
        for subject_id in prepare["subject_ids"]:
            require_id(subject_id)
        require(len(set(prepare["subject_ids"])) == 26,
                "PREPARE opaque ids must be unique")
        require(prepare["subject_ids"] == sorted(prepare["subject_ids"]),
                "PREPARE opaque ids must use canonical order")

        finalize_keys = COMMON_KEYS | {
            "audit", "audit_root", "externally_pinned_prepare_root",
            "labels_commitment", "prepare_root", "query_domain_root",
            "subject_commitment", "subject_ids",
        }
        require_exact_keys(finalize, finalize_keys, "FINALIZE payload")
        require(not has_secret_field(finalize), "FINALIZE discloses a secret field")
        require(finalize["phase"] == "FINALIZE" and finalize["sequence"] == 1,
                "FINALIZE phase or sequence mismatch")
        require(finalize["protocol"] == PROTOCOL and finalize["authority"] == AUTHORITY,
                "FINALIZE protocol or authority mismatch")
        require(finalize["run_id"] == prepare["run_id"], "FINALIZE run splice")
        require(finalize["run_mode"] == prepare["run_mode"], "FINALIZE mode splice")
        require(finalize["trust_anchor_root"] == anchor_root,
                "FINALIZE trust-anchor root mismatch")
        require(finalize["prior_root"] == actual_prepare and finalize["prepare_root"] == actual_prepare,
                "FINALIZE does not bind PREPARE")
        require(finalize["externally_pinned_prepare_root"] == expected_prepare,
                "FINALIZE did not consume pinned PREPARE root")
        for field in ("source_root", "query_domain_root", "subject_commitment", "labels_commitment", "subject_ids"):
            require(finalize[field] == prepare[field], f"FINALIZE {field} mismatch")
        checked_audit = validate_audit(finalize["audit"], prepare["subject_ids"])
        require(finalize["audit_root"] == domain_hash("CZ3-AUDIT-v1", checked_audit),
                "FINALIZE audit root mismatch")

        reveal_keys = COMMON_KEYS | {
            "externally_pinned_finalize_root", "externally_pinned_prepare_root",
            "finalize_root", "fixture_result", "labels_commitment", "opening",
            "prepare_root", "query_domain_root", "subject_commitment", "subject_ids",
        }
        require_exact_keys(reveal, reveal_keys, "REVEAL payload")
        require(reveal["phase"] == "REVEAL" and reveal["sequence"] == 2,
                "REVEAL phase or sequence mismatch")
        require(reveal["protocol"] == PROTOCOL and reveal["authority"] == AUTHORITY,
                "REVEAL protocol or authority mismatch")
        require(reveal["run_id"] == prepare["run_id"], "REVEAL run splice")
        require(reveal["run_mode"] == prepare["run_mode"], "REVEAL mode splice")
        require(reveal["trust_anchor_root"] == anchor_root,
                "REVEAL trust-anchor root mismatch")
        require(reveal["prior_root"] == actual_finalize and reveal["finalize_root"] == actual_finalize,
                "REVEAL does not bind FINALIZE")
        require(reveal["prepare_root"] == actual_prepare,
                "REVEAL does not carry PREPARE root")
        require(reveal["externally_pinned_prepare_root"] == expected_prepare,
                "REVEAL PREPARE pin mismatch")
        require(reveal["externally_pinned_finalize_root"] == expected_finalize,
                "REVEAL did not consume pinned FINALIZE root")
        for field in ("source_root", "query_domain_root", "subject_commitment", "labels_commitment", "subject_ids"):
            require(reveal[field] == prepare[field], f"REVEAL {field} mismatch")

        opening = require_exact_keys(
            reveal["opening"], {"label_nonce", "labels", "subject_nonce", "subjects"},
            "REVEAL opening",
        )
        subject_nonce = require_hex(opening["subject_nonce"], 32, "subject nonce")
        label_nonce = require_hex(opening["label_nonce"], 32, "label nonce")
        require(subject_nonce != label_nonce, "subject and label nonces must differ")
        subjects, labels = validate_population(opening["subjects"], opening["labels"])
        require(sorted(x["id"] for x in subjects) == prepare["subject_ids"],
                "revealed subject ids mismatch")
        require(subject_commitment(prepare["run_id"], subject_nonce, subjects) == prepare["subject_commitment"],
                "subject commitment opening mismatch")
        require(labels_commitment(prepare["run_id"], label_nonce, labels) == prepare["labels_commitment"],
                "label commitment opening mismatch")

        expected_audit = audit_from_specs(subjects)
        require(checked_audit == expected_audit,
                "revealed subjects do not replay the FINALIZE audit exactly")
        audit_by_id = {row["id"]: row for row in checked_audit["subjects"]}
        correct = sum(
            audit_by_id[sid]["verdict"] == label["truth"]
            and audit_by_id[sid]["witness"] == label["witness"]
            for sid, label in labels.items()
        )
        expected_result = {
            "all_exact": correct == len(labels),
            "correct": correct,
            "qualification": "TEST_FIXTURE_CONSISTENT_AUTHORITY_NONE",
            "total": len(labels),
        }
        require(reveal["fixture_result"] == expected_result,
                "fixture result mismatch")
        return {
            "authority": AUTHORITY,
            "errors": [],
            "ok": True,
            "phase_roots": {
                "FINALIZE": actual_finalize,
                "PREPARE": actual_prepare,
                "REVEAL": actual_reveal,
            },
            "qualification": expected_result["qualification"],
        }
    except Exception as exc:
        return {
            "authority": AUTHORITY,
            "errors": [f"{type(exc).__name__}: {exc}"],
            "ok": False,
            "qualification": "REFUSED_AUTHORITY_NONE",
        }


def read_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_bytes().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript_dir", type=pathlib.Path)
    parser.add_argument("--trust-anchor", required=True, type=pathlib.Path)
    parser.add_argument("--prepare-root", required=True)
    parser.add_argument("--finalize-root", required=True)
    parser.add_argument("--source-dir", type=pathlib.Path, default=pathlib.Path(__file__).parent)
    args = parser.parse_args()
    transcript = args.transcript_dir
    result = verify_transcript(
        read_json(args.trust_anchor),
        read_json(transcript / "PREPARE.json"),
        read_json(transcript / "FINALIZE.json"),
        read_json(transcript / "REVEAL.json"),
        args.prepare_root,
        args.finalize_root,
        args.source_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
