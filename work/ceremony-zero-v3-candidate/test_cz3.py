#!/usr/bin/env python3
"""Exhaustive conformance and hostile refusal tests for the v3 candidate."""

from __future__ import annotations

import copy
import inspect
import pathlib
import random
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import cz3_core as core
import make_test_fixture as fixture_builder


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.fx = fixture_builder.build_fixture()

    def verify(self, fx=None):
        item = fx or self.fx
        return core.verify_transcript(
            item["anchor"], item["prepare"], item["finalize"], item["reveal"],
            item["pins"]["PREPARE"], item["pins"]["FINALIZE"], HERE,
        )

    def test_known_answer_fixture_is_consistent_but_authority_none(self):
        result = self.verify()
        self.assertTrue(result["ok"], result)
        self.assertEqual(core.AUTHORITY, result["authority"])
        self.assertEqual("TEST_FIXTURE_CONSISTENT_AUTHORITY_NONE", result["qualification"])
        self.assertNotIn("ceremony_go", str(self.fx).lower())

    def test_complete_26_policy_population_classifies_exactly(self):
        audit = core.audit_from_specs(self.fx["subjects"])
        by_id = {row["id"]: row for row in audit["subjects"]}
        self.assertEqual(26, len(by_id))
        self.assertEqual(60, len(core.query_domain()))
        for spec in self.fx["subjects"]:
            self.assertEqual(core.expected_label(spec)["truth"], by_id[spec["id"]]["verdict"])
            self.assertEqual(core.expected_label(spec)["witness"], by_id[spec["id"]]["witness"])
            self.assertEqual("UNIQUE_FINITE_CLASS_MATCH", by_id[spec["id"]]["reason"])

    def test_out_of_class_behavior_returns_unknown(self):
        responses = [
            {"input": triple, "output": [(triple[1] + 2) % 3, triple[2]]}
            for triple in core.query_domain()
        ]
        result = core.classify_responses(responses)
        self.assertEqual("UNKNOWN", result["verdict"])
        self.assertEqual("NO_FINITE_CLASS_MATCH", result["reason"])

    def test_oracle_failure_returns_unknown_without_exception_text(self):
        def broken(prev, sym, flag):
            raise RuntimeError("secret exception detail")

        healthy = {
            spec["id"]: (lambda prev, sym, flag, held=spec: core.query_spec(held, prev, sym, flag))
            for spec in self.fx["subjects"]
        }
        healthy[sorted(healthy)[0]] = broken
        audit = core.audit_oracles(healthy)
        first = audit["subjects"][0]
        self.assertEqual("UNKNOWN", first["verdict"])
        self.assertNotIn("secret exception detail", str(first))

    def test_prepare_and_finalize_contain_no_opening_or_ground_truth(self):
        self.assertFalse(core.has_secret_field(self.fx["prepare"]["payload"]))
        self.assertFalse(core.has_secret_field(self.fx["finalize"]["payload"]))
        text = str(self.fx["prepare"]["payload"]).lower()
        for inherited in ("drand", "randomness", "escrow", "reveal_round", "corpus", "seed"):
            self.assertNotIn(inherited, text)

    def test_finalize_builder_has_no_labels_argument(self):
        parameters = inspect.signature(fixture_builder.build_finalize).parameters
        self.assertNotIn("labels", parameters)
        self.assertNotIn("label_nonce", parameters)

    def test_private_subject_commitment_is_checked_before_first_query(self):
        subjects = copy.deepcopy(self.fx["subjects"])
        triggered = [x for x in subjects if x["kind"] == "BIGRAM_PERSISTENT"]
        triggered[0]["trigger"], triggered[1]["trigger"] = triggered[1]["trigger"], triggered[0]["trigger"]
        opening = self.fx["reveal"]["payload"]["opening"]
        with mock.patch.object(core, "audit_from_specs") as audit:
            with self.assertRaises(core.Refusal):
                fixture_builder.build_finalize(
                    self.fx["prepare"], self.fx["pins"]["PREPARE"], subjects,
                    opening["subject_nonce"], self.fx["private_key"],
                )
            audit.assert_not_called()

    def test_nonce_hides_low_entropy_labels_and_is_strict(self):
        run_id = self.fx["prepare"]["payload"]["run_id"]
        label_commitment = self.fx["prepare"]["payload"]["labels_commitment"]
        unsalted = core.domain_hash("CZ3-LABEL-COMMITMENT-v1", self.fx["labels"])
        self.assertNotEqual(unsalted, label_commitment)
        for guess in range(256):
            wrong_nonce = guess.to_bytes(32, "big").hex()
            self.assertNotEqual(
                label_commitment,
                core.labels_commitment(run_id, wrong_nonce, self.fx["labels"]),
            )
        with self.assertRaises(core.Refusal):
            core.labels_commitment(run_id, "00" * 31, self.fx["labels"])

    def test_same_opening_is_domain_and_run_separated(self):
        opening = self.fx["reveal"]["payload"]["opening"]
        run_id = self.fx["prepare"]["payload"]["run_id"]
        subject_value = core.commitment(
            "CZ3-SUBJECT-COMMITMENT-v1", run_id, opening["subject_nonce"], self.fx["labels"]
        )
        label_value = core.labels_commitment(run_id, opening["subject_nonce"], self.fx["labels"])
        other_run = core.subject_commitment(run_id + "-OTHER", opening["subject_nonce"], opening["subjects"])
        self.assertNotEqual(subject_value, label_value)
        self.assertNotEqual(subject_value, other_run)

    def test_wrong_external_prepare_root_is_rejected(self):
        self.fx["pins"]["PREPARE"] = "00" * 32
        result = self.verify()
        self.assertFalse(result["ok"])
        self.assertIn("not externally pinned", result["errors"][0])

    def test_wrong_external_finalize_root_is_rejected(self):
        self.fx["pins"]["FINALIZE"] = "00" * 32
        result = self.verify()
        self.assertFalse(result["ok"])
        self.assertIn("not externally pinned", result["errors"][0])

    def test_custodian_key_substitution_is_rejected(self):
        replacement = Ed25519PrivateKey.generate()
        self.fx["anchor"]["ed25519_public_key"] = core.public_key_hex(replacement)
        result = self.verify()
        self.assertFalse(result["ok"])
        self.assertTrue(
            "trust-anchor root mismatch" in result["errors"][0]
            or "signer key mismatch" in result["errors"][0]
        )

    def test_finalize_verdict_substitution_is_rejected_even_if_resigned_and_repinned(self):
        key = self.fx["private_key"]
        payload = copy.deepcopy(self.fx["finalize"]["payload"])
        target = next(row for row in payload["audit"]["subjects"] if row["verdict"] == "ABSENT")
        target["verdict"] = "PRESENT"
        target["witness"] = [0, 0]
        payload["audit_root"] = core.domain_hash("CZ3-AUDIT-v1", payload["audit"])
        altered_finalize = core.sign_record(payload, key)
        altered_root = core.record_root(altered_finalize)
        self.fx["finalize"] = altered_finalize
        self.fx["pins"]["FINALIZE"] = altered_root
        reveal_payload = copy.deepcopy(self.fx["reveal"]["payload"])
        reveal_payload["prior_root"] = altered_root
        reveal_payload["finalize_root"] = altered_root
        reveal_payload["externally_pinned_finalize_root"] = altered_root
        self.fx["reveal"] = core.sign_record(reveal_payload, key)
        result = self.verify()
        self.assertFalse(result["ok"])
        self.assertIn("audit verdict mismatch", result["errors"][0])

    def test_query_response_substitution_is_rejected(self):
        key = self.fx["private_key"]
        payload = copy.deepcopy(self.fx["finalize"]["payload"])
        response = payload["audit"]["subjects"][0]["responses"][0]["output"]
        response[0] = (response[0] + 1) % 3
        payload["audit_root"] = core.domain_hash("CZ3-AUDIT-v1", payload["audit"])
        altered_finalize = core.sign_record(payload, key)
        altered_root = core.record_root(altered_finalize)
        self.fx["finalize"] = altered_finalize
        self.fx["pins"]["FINALIZE"] = altered_root
        reveal_payload = copy.deepcopy(self.fx["reveal"]["payload"])
        reveal_payload["prior_root"] = altered_root
        reveal_payload["finalize_root"] = altered_root
        reveal_payload["externally_pinned_finalize_root"] = altered_root
        self.fx["reveal"] = core.sign_record(reveal_payload, key)
        result = self.verify()
        self.assertFalse(result["ok"])

    def test_query_drop_and_reorder_are_rejected(self):
        original = self.fx["finalize"]["payload"]["audit"]["subjects"][0]["responses"]
        for mutated in (original[:-1], [original[1], original[0], *original[2:]]):
            classification = core.classify_responses(copy.deepcopy(mutated))
            self.assertEqual("UNKNOWN", classification["verdict"])

    def test_revealed_subject_substitution_is_rejected(self):
        key = self.fx["private_key"]
        payload = copy.deepcopy(self.fx["reveal"]["payload"])
        triggered = [x for x in payload["opening"]["subjects"] if x["kind"] == "BIGRAM_PERSISTENT"]
        triggered[0]["trigger"], triggered[1]["trigger"] = triggered[1]["trigger"], triggered[0]["trigger"]
        labels = payload["opening"]["labels"]
        labels[triggered[0]["id"]], labels[triggered[1]["id"]] = labels[triggered[1]["id"]], labels[triggered[0]["id"]]
        self.fx["reveal"] = core.sign_record(payload, key)
        result = self.verify()
        self.assertFalse(result["ok"])
        self.assertIn("subject commitment opening mismatch", result["errors"][0])

    def test_wrong_or_reused_opening_nonce_is_rejected(self):
        key = self.fx["private_key"]
        payload = copy.deepcopy(self.fx["reveal"]["payload"])
        payload["opening"]["label_nonce"] = payload["opening"]["subject_nonce"]
        self.fx["reveal"] = core.sign_record(payload, key)
        result = self.verify()
        self.assertFalse(result["ok"])
        self.assertIn("nonces must differ", result["errors"][0])

    def test_cross_run_phase_splice_is_rejected(self):
        other = fixture_builder.build_fixture("CZ3-TEST-ONLY-RUN-OTHER")
        self.fx["finalize"] = other["finalize"]
        self.fx["pins"]["FINALIZE"] = other["pins"]["FINALIZE"]
        result = self.verify()
        self.assertFalse(result["ok"])

    def test_source_substitution_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = pathlib.Path(tmp)
            for rel in core.SOURCE_FILES:
                shutil.copy2(HERE / rel, temp / rel)
            (temp / "cz3_core.py").write_bytes((temp / "cz3_core.py").read_bytes() + b"\n# substitution\n")
            result = core.verify_transcript(
                self.fx["anchor"], self.fx["prepare"], self.fx["finalize"], self.fx["reveal"],
                self.fx["pins"]["PREPARE"], self.fx["pins"]["FINALIZE"], temp,
            )
        self.assertFalse(result["ok"])
        self.assertIn("source manifest mismatch", result["errors"][0])

    def test_complete_phase_chain_is_carried_to_reveal(self):
        prepare_root = core.record_root(self.fx["prepare"])
        finalize_root = core.record_root(self.fx["finalize"])
        finalize = self.fx["finalize"]["payload"]
        reveal = self.fx["reveal"]["payload"]
        self.assertEqual(prepare_root, finalize["prior_root"])
        self.assertEqual(prepare_root, finalize["prepare_root"])
        self.assertEqual(finalize_root, reveal["prior_root"])
        self.assertEqual(finalize_root, reveal["finalize_root"])
        self.assertEqual(prepare_root, reveal["prepare_root"])
        self.assertEqual(self.fx["prepare"]["payload"]["source_root"], reveal["source_root"])

    def test_total_verifier_refuses_malformed_inputs_without_throwing(self):
        rng = random.Random(20260827)
        atoms = [None, True, False, 0, 1, -1, "", "00", [], {}, {"payload": None}]
        for _ in range(500):
            values = [copy.deepcopy(rng.choice(atoms)) for _ in range(6)]
            result = core.verify_transcript(*values, HERE)
            self.assertIsInstance(result, dict)
            self.assertFalse(result["ok"])
            self.assertEqual("REFUSED_AUTHORITY_NONE", result["qualification"])


if __name__ == "__main__":
    unittest.main()
