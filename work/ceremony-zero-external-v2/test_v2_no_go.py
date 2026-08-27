#!/usr/bin/env python3
"""Reproduce the frozen Ceremony Zero External v2 NO-GO findings.

These tests pass only when the published v2 vulnerabilities remain
reproducible. They are hostile closure evidence, not tests of a repaired v3.
"""

import base64
import hashlib
import importlib.util
import itertools
import json
import pathlib
import shutil
import tempfile
import unittest


HERE = pathlib.Path(__file__).resolve().parent
RUN = HERE / "run2"
SECRET = HERE / "SECRET"


def load_runner():
    spec = importlib.util.spec_from_file_location("cz2_frozen_runner", HERE / "cz2_runner.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


RUNNER = load_runner()


def read_json(path):
    return json.loads(path.read_bytes().decode("utf-8"))


class FrozenV2NoGoTests(unittest.TestCase):
    def test_prepare_label_commitment_is_bruteforceable(self):
        registry = read_json(RUN / "prepare" / "registry.json")
        target = registry["labels_sha256"]
        values = [{"truth": "ABSENT", "witness": None}]
        values.extend(
            {"truth": "PRESENT", "witness": [a, b]}
            for a in range(5)
            for b in range(5)
        )

        recovered = None
        tries = 0
        for candidate_values in itertools.product(values, repeat=3):
            candidate = {
                "S0": candidate_values[0],
                "S1": candidate_values[1],
                "S2": candidate_values[2],
            }
            blob = json.dumps(candidate, indent=2, sort_keys=True).encode("utf-8")
            tries += 1
            if hashlib.sha256(blob).hexdigest() == target:
                recovered = candidate
                break

        self.assertIsNotNone(recovered)
        self.assertEqual(608, tries)
        self.assertEqual(read_json(SECRET / "labels_plain.json"), recovered)

    def test_public_escrow_decrypts_before_reveal(self):
        registry = read_json(RUN / "prepare" / "registry.json")
        challenge = read_json(RUN / "challenge" / "corpus_record.json")
        escrow = read_json(RUN / "escrow" / "labels.masked.json")

        ciphertext = base64.b64decode(escrow["masked_b64"])
        seed = hashlib.sha256(bytes.fromhex(challenge["challenge_randomness"])).hexdigest()
        mask = RUNNER.keystream(seed, len(ciphertext))
        plaintext = bytes(a ^ b for a, b in zip(ciphertext, mask))

        self.assertEqual(registry["labels_sha256"], hashlib.sha256(plaintext).hexdigest())
        self.assertEqual(read_json(SECRET / "labels_plain.json"), json.loads(plaintext.decode("utf-8")))

    def test_challenge_round_signature_is_accepted_as_reveal_signature(self):
        challenge_round = 6_407_783
        committed_reveal_round = challenge_round + RUNNER.REVEAL_OFFSET
        previous_signature = (
            "a206a15239a1a6c9ae25e62d8d46a5b5c6c5246b060535b57523ac588bbc7ad8"
            "b2261910d17d23dcb1316a97c6a623030e7e2b9e2b1d23e1eaf6e380b3fce08e"
            "ae031ac00463138db16e82950b68e082d9738094452e8a924b65603df1a841b3"
        )
        challenge_signature = (
            "a21eccd0c6314dcadbcc4dbd30e16c39446d9804445c34367d338ae06e4dd126"
            "d4503cb6511f79eeb598edd84527889e19832134abf76b8f5e3ae8742bf4a473a"
            "10f8f8a1dd2a386bb19f343b1583c9b3b2f75ce25cfb0b4bf0b0b7f92142cac"
        )

        self.assertNotEqual(challenge_round, committed_reveal_round)
        self.assertTrue(
            RUNNER.verify_bls_reveal(
                challenge_round,
                previous_signature,
                challenge_signature,
            )
        )

    def test_valid_corpus_seed_53_produces_false_witness(self):
        query = RUNNER.load_subject_module(str(SECRET / "S1.py"), "seed53_S1")
        _, streams = RUNNER.build_corpus(f"{53:064x}")
        verdict = RUNNER.audit_streams(query, streams)
        self.assertEqual("PRESENT", verdict["verdict"])
        self.assertEqual([2, 4], verdict["witness"])
        self.assertNotEqual([4, 2], verdict["witness"])

    def test_valid_corpus_seed_61_produces_false_witness(self):
        query = RUNNER.load_subject_module(str(SECRET / "S1.py"), "seed61_S1")
        _, streams = RUNNER.build_corpus(f"{61:064x}")
        verdict = RUNNER.audit_streams(query, streams)
        self.assertEqual("PRESENT", verdict["verdict"])
        self.assertEqual([2, 1], verdict["witness"])
        self.assertNotEqual([4, 2], verdict["witness"])

    def test_audit_accepts_subject_bytes_that_do_not_match_registry(self):
        original_run = RUNNER.RUN
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            run_path = tmp_path / "run2"
            secret_path = tmp_path / "secret"
            (run_path / "prepare").mkdir(parents=True)
            (run_path / "challenge").mkdir(parents=True)
            secret_path.mkdir()
            shutil.copy2(RUN / "prepare" / "registry.json", run_path / "prepare" / "registry.json")
            shutil.copy2(
                RUN / "challenge" / "corpus_record.json",
                run_path / "challenge" / "corpus_record.json",
            )
            for subject in ("S0.py", "S1.py", "S2.py"):
                shutil.copy2(SECRET / subject, secret_path / subject)
            (secret_path / "S0.py").write_bytes(
                b"def query(prev_sym, sym, flag):\n    return (sym + 2) % 3, flag\n"
            )

            committed = read_json(run_path / "prepare" / "registry.json")["subjects"][0]["sha256"]
            substituted = hashlib.sha256((secret_path / "S0.py").read_bytes()).hexdigest()
            self.assertNotEqual(committed, substituted)

            try:
                RUNNER.RUN = str(run_path)
                RUNNER.cmd_audit("SUBSTITUTED", str(secret_path))
            finally:
                RUNNER.RUN = original_run

            self.assertTrue((run_path / "audit_SUBSTITUTED" / "verdicts.json").is_file())

    def test_finalize_binds_only_the_two_local_verdict_files(self):
        finalize = read_json(RUN / "finalize" / "FINALIZE.json")
        self.assertEqual(
            {"audit_A/verdicts.json", "audit_B/verdicts.json"},
            set(finalize["replica_roots"]),
        )
        for required_root in (
            "prepare_root",
            "challenge_root",
            "escrow_root",
            "runner_code_sha256",
            "subject_root",
            "published_finalize_receipt",
        ):
            self.assertNotIn(required_root, finalize)

    def test_result_omits_the_upstream_phase_chain(self):
        result = read_json(RUN / "reveal" / "RESULT.json")
        for required_root in (
            "prepare_root",
            "challenge_root",
            "escrow_root",
            "finalize_root",
            "runner_code_sha256",
            "subject_root",
        ):
            self.assertNotIn(required_root, result)


if __name__ == "__main__":
    unittest.main()
