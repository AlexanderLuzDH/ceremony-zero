#!/usr/bin/env python3
"""Create the deterministic TEST_ONLY v3 conformance transcript.

This generator is not a custody implementation. Its key, nonces, subjects,
and labels are deliberately reproducible and public.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import cz3_core as core


HERE = pathlib.Path(__file__).resolve().parent
TEST_RUN_MODE = "TEST_ONLY_KNOWN_ANSWER_SIMULATION"
TEST_CUSTODIAN = "TEST_ONLY_LOCAL_FIXTURE_NOT_INDEPENDENT"


def test_private_key() -> Ed25519PrivateKey:
    seed = hashlib.sha256(b"CZ3 deterministic TEST_ONLY signing key v1").digest()
    return Ed25519PrivateKey.from_private_bytes(seed)


def deterministic_nonce(label: bytes) -> str:
    return hashlib.sha256(b"CZ3 deterministic TEST_ONLY nonce v1\x00" + label).hexdigest()


def test_population() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    templates: list[dict[str, Any]] = [{"kind": "CLEAN", "trigger": None}]
    templates.extend(
        {"kind": "BIGRAM_PERSISTENT", "trigger": [a, b]}
        for a in range(core.ALPHABET)
        for b in range(core.ALPHABET)
    )
    templates.sort(
        key=lambda item: hashlib.sha256(
            b"CZ3 TEST_ONLY permutation v1\x00" + core.canonical_json(item)
        ).digest()
    )
    subjects = []
    for index, item in enumerate(templates):
        opaque_id = hashlib.sha256(
            b"CZ3 deterministic TEST_ONLY opaque id v1\x00" + index.to_bytes(2, "big")
        ).hexdigest()[:32]
        subjects.append({"id": opaque_id, "kind": item["kind"], "trigger": item["trigger"]})
    labels = {item["id"]: core.expected_label(item) for item in subjects}
    core.validate_population(subjects, labels)
    return subjects, labels


def build_finalize(
    prepare_record: dict[str, Any],
    externally_pinned_prepare_root: str,
    subjects: list[dict[str, Any]],
    subject_nonce: str,
    private_key: Ed25519PrivateKey,
) -> dict[str, Any]:
    """TEST_ONLY custody adapter; labels are intentionally not an argument."""
    prepare = prepare_record["payload"]
    recomputed = core.subject_commitment(prepare["run_id"], subject_nonce, subjects)
    core.require(recomputed == prepare["subject_commitment"],
                 "private subject bundle does not match PREPARE")
    audit = core.audit_from_specs(subjects)
    payload = {
        "audit": audit,
        "audit_root": core.domain_hash("CZ3-AUDIT-v1", audit),
        "authority": core.AUTHORITY,
        "externally_pinned_prepare_root": externally_pinned_prepare_root,
        "labels_commitment": prepare["labels_commitment"],
        "phase": "FINALIZE",
        "prepare_root": core.record_root(prepare_record),
        "prior_root": core.record_root(prepare_record),
        "protocol": core.PROTOCOL,
        "query_domain_root": prepare["query_domain_root"],
        "run_id": prepare["run_id"],
        "run_mode": prepare["run_mode"],
        "sequence": 1,
        "source_root": prepare["source_root"],
        "subject_commitment": prepare["subject_commitment"],
        "subject_ids": prepare["subject_ids"],
        "trust_anchor_root": prepare["trust_anchor_root"],
    }
    return core.sign_record(payload, private_key)


def build_fixture(run_id: str = "CZ3-TEST-ONLY-RUN-001") -> dict[str, Any]:
    private_key = test_private_key()
    subjects, labels = test_population()
    subject_nonce = deterministic_nonce(b"subjects")
    label_nonce = deterministic_nonce(b"labels")
    manifest = core.source_manifest(HERE)
    anchor = {
        "authority": core.AUTHORITY,
        "candidate_source_root": core.source_root(manifest),
        "custodian_id": TEST_CUSTODIAN,
        "ed25519_public_key": core.public_key_hex(private_key),
        "kind": "CEREMONY_ZERO_V3_EXTERNAL_TRUST_ANCHOR",
        "run_mode": TEST_RUN_MODE,
        "source_manifest": manifest,
    }
    subject_ids = sorted(item["id"] for item in subjects)
    prepare_payload = {
        "authority": core.AUTHORITY,
        "commitment_scheme": core.COMMITMENT_SCHEME,
        "labels_commitment": core.labels_commitment(run_id, label_nonce, labels),
        "phase": "PREPARE",
        "prior_root": None,
        "protocol": core.PROTOCOL,
        "query_domain_root": core.query_domain_root(),
        "run_id": run_id,
        "run_mode": TEST_RUN_MODE,
        "sequence": 0,
        "source_manifest": manifest,
        "source_root": core.source_root(manifest),
        "subject_commitment": core.subject_commitment(run_id, subject_nonce, subjects),
        "subject_ids": subject_ids,
        "trust_anchor_root": core.trust_anchor_root(anchor),
    }
    prepare_record = core.sign_record(prepare_payload, private_key)
    prepare_root = core.record_root(prepare_record)
    finalize_record = build_finalize(
        prepare_record, prepare_root, subjects, subject_nonce, private_key
    )
    finalize_root = core.record_root(finalize_record)
    audit_by_id = {row["id"]: row for row in finalize_record["payload"]["audit"]["subjects"]}
    correct = sum(
        audit_by_id[sid]["verdict"] == label["truth"]
        and audit_by_id[sid]["witness"] == label["witness"]
        for sid, label in labels.items()
    )
    reveal_payload = {
        "authority": core.AUTHORITY,
        "externally_pinned_finalize_root": finalize_root,
        "externally_pinned_prepare_root": prepare_root,
        "finalize_root": finalize_root,
        "fixture_result": {
            "all_exact": correct == len(labels),
            "correct": correct,
            "qualification": "TEST_FIXTURE_CONSISTENT_AUTHORITY_NONE",
            "total": len(labels),
        },
        "labels_commitment": prepare_payload["labels_commitment"],
        "opening": {
            "label_nonce": label_nonce,
            "labels": labels,
            "subject_nonce": subject_nonce,
            "subjects": subjects,
        },
        "phase": "REVEAL",
        "prepare_root": prepare_root,
        "prior_root": finalize_root,
        "protocol": core.PROTOCOL,
        "query_domain_root": prepare_payload["query_domain_root"],
        "run_id": run_id,
        "run_mode": TEST_RUN_MODE,
        "sequence": 2,
        "source_root": prepare_payload["source_root"],
        "subject_commitment": prepare_payload["subject_commitment"],
        "subject_ids": subject_ids,
        "trust_anchor_root": prepare_payload["trust_anchor_root"],
    }
    reveal_record = core.sign_record(reveal_payload, private_key)
    return {
        "anchor": anchor,
        "finalize": finalize_record,
        "labels": labels,
        "pins": {"FINALIZE": finalize_root, "PREPARE": prepare_root},
        "prepare": prepare_record,
        "private_key": private_key,
        "reveal": reveal_record,
        "subjects": subjects,
    }


def write_json(path: pathlib.Path, value: Any) -> None:
    data = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"
    path.write_bytes(data)


def write_fixture(output_dir: pathlib.Path) -> dict[str, Any]:
    fixture = build_fixture()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "TRUST_ANCHOR.json", fixture["anchor"])
    write_json(output_dir / "PREPARE.json", fixture["prepare"])
    write_json(output_dir / "FINALIZE.json", fixture["finalize"])
    write_json(output_dir / "REVEAL.json", fixture["reveal"])
    write_json(
        output_dir / "PINNED_ROOTS.json",
        {
            "authority": core.AUTHORITY,
            "note": "TEST_ONLY self-recorded roots; not external chronology evidence",
            **fixture["pins"],
        },
    )
    return fixture


def main() -> int:
    output = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "test_fixture"
    fixture = write_fixture(output)
    result = core.verify_transcript(
        fixture["anchor"], fixture["prepare"], fixture["finalize"], fixture["reveal"],
        fixture["pins"]["PREPARE"], fixture["pins"]["FINALIZE"], HERE,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
