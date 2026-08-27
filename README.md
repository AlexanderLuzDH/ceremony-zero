# Ceremony Zero

**Current status: v2 and the one permitted pre-custody v3 candidate are frozen
NO-GO. This repository is a transparent failure-and-repair record, not a
completed blind referee.**

Ceremony Zero asks whether a fixed auditor can judge hidden behavior against
ground truth it cannot access before its verdicts are finalized. The project
has produced real, replayable engineering evidence—and has repeatedly shown
how easy it is to mistake chronology and deterministic execution for
blindness.

## Bottom line

The local ceremony caught a false-witness bug in its own auditor. The external
run established public GitHub/drand ordering and local BLS verification. A
hostile review then broke v1. V2 attempted the repairs and ran 3/3, but a fresh
hostile audit found that v2 still leaks labels before FINALIZE, does not bind
the reveal round, returns false witnesses for valid corpus seeds, and does not
enforce complete subject/phase identity.

The exact v2 verdict and executable counterexamples are in
[`V2_NO_GO.md`](work/ceremony-zero-external-v2/V2_NO_GO.md).

One separately chartered, authority-`NONE` v3 candidate then removed the
unnecessary beacon, escrow, random corpus, and executable-subject machinery.
Its exhaustive finite auditor passed all 26 policies, but the post-freeze
hostile review found that the verifier accepted short whitespace-padded nonces,
crashed on malformed public JSON, and did not bind duplicate-key JSON bytes
unambiguously. It is preserved as
[`FROZEN_V3_CANDIDATE_NO_GO`](work/ceremony-zero-v3-candidate/FREEZE.md), not
silently repaired.

## Version record

| Version | What it established | Current verdict |
|---|---|---|
| Local v1 auditor | Preserved false witnesses and a 1/3 score | Failed, useful negative result |
| Local repaired auditor | 3/3 on three author-built toy policies; byte-identical replay | Bounded local path-blind demonstration only |
| External v1 | Immutable public chronology and BLS-verifiable drand evidence | Failed hostile review |
| External v2 | Attempted blind registry, escrow, reveal, FINALIZE, and byte-pinning repairs; actual run 3/3 | **Frozen NO-GO** |
| Pre-custody v3 candidate | Exhaustive 26-policy relation, hiding commitments, signed phase chain, total-verifier attempt; TEST_ONLY fixture 26/26 | **Frozen NO-GO after post-freeze hostile review; authority NONE** |

## Reproduce the v2 failures

Install Python 3.11+ and the one cryptographic dependency:

```console
python -m pip install -r requirements.txt
python -B -m unittest -v work/ceremony-zero-external-v2/test_v2_no_go.py
```

The eight tests are expected to pass because they reproduce these failures:

1. the PREPARE label hash reveals the low-entropy ground truth in 608 guesses;
2. the public escrow decrypts using already-public challenge randomness;
3. the challenge-round signature is accepted as a reveal signature even
   though the committed reveal round is twelve rounds later;
4. valid corpus seeds 53 and 61 yield false witnesses;
5. audit accepts subject bytes that do not match the registry commitment; and
6. the published phase artifacts do not form a complete enforced state chain.

## What remains valid

- The original local failure is preserved rather than hidden.
- The repaired local run scored 3/3 and still replays byte-identically.
- The published release timestamps record the actual external chronology.
- The cited drand values have valid BLS signatures against the pinned chain
  key.
- V2's historical runner, artifacts, releases, and 3/3 result remain available
  for replay and attack.

Those facts do **not** imply label secrecy, independent custody, auditor
soundness, or a machine-enforced reveal chronology.

## Historical public receipts

These v1 receipts establish what was published when; they do not establish
that the answers remained secret.

| Time (UTC) | Event | Receipt |
|---|---|---|
| 2026-08-24T11:04:49Z | PREPARE committed | [release](https://github.com/AlexanderLuzDH/perfect-digital-referee-custody/releases/tag/ceremony-zero-ext-v1-prepare-9d412ae4ab0f7806e5b24748f2f92023f45b75df11351cf261693077c31892b4) |
| +191s | drand challenge round `6404621` | BLS evidence preserved in the repository |
| 2026-08-24T11:09:46Z | FINALIZE released | [release](https://github.com/AlexanderLuzDH/perfect-digital-referee-custody/releases/tag/ceremony-zero-ext-v1-finalize-6cd2d41502c2ae5a6d7353fbe376e928f9b6d86ef35c5045e9ae538345fa0402) |
| +74s | drand reveal round `6404627` | BLS evidence preserved in the repository |
| 2026-08-24T11:11:22Z | RESULT: 3/3 | [release](https://github.com/AlexanderLuzDH/perfect-digital-referee-custody/releases/tag/ceremony-zero-ext-v1-result-0a036845775b70fe39c8fac2c72bde5be287ae95288261218e44d9372e9487c8) |

## Next gate: stop unless a new repair decision is made

Hosted-runner work is stopped. The same implementation on GitHub Actions would
add environment diversity while reproducing a relation already known to be
invalid. It would add neither independent implementation nor independent
custody, and GitHub Releases plus GitHub Actions are not provider-diverse.

The one permitted solo candidate cycle is complete and terminal NO-GO. Its
charter forbids patching the frozen bytes after review. A repair generation
requires a new explicit decision; a later evidence-producing run still
requires an independently administered custodian holding subjects, labels, and
fresh nonces outside the author's pre-reveal access.

Until both decisions exist, there is no runnable v3 candidate and no claim to
take to a custodian. V2 and the pre-custody candidate are the honest stopping
points.

## Repository layout

```text
work/ceremony-zero-v1/
  ceremony.py                       local implementation and replay
  run_v1_audit_false_witness_FAILURE/  preserved 1/3 failure
  run/                              repaired 3/3 local result

work/ceremony-zero-external-v1/
  ext_ceremony.py                   historical external chronology
  verify_bls.py                     drand BLS verification
  run/                              preserved public-run artifacts

work/ceremony-zero-external-v2/
  cz2_runner.py                     frozen failed v2 runner
  run2/                             preserved 3/3 v2 artifacts
  V2_NO_GO.md                       hostile closure record
  V2_NO_GO.json                     machine-readable verdict
  test_v2_no_go.py                  executable counterexamples
  V3_CUSTODY_GATE.md                resume conditions; no v3 authority
  CO_CUSTODIAN_BRIEF.md             bounded request for a second custodian

work/ceremony-zero-v3-candidate/
  CHARTER.md                         one-cycle authority-NONE charter
  cz3_core.py                        frozen exhaustive auditor/verifier candidate
  test_cz3.py                        21 conformance and hostile tests
  SOURCE_FREEZE.json                 exact 12-file source/fixture inventory
  HOSTILE_REVIEW.md                  internal post-freeze attack record
  FREEZE.md                          terminal v3 candidate NO-GO
```

## License

MIT
