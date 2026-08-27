# Ceremony Zero

**Current status: v2 is a frozen NO-GO. This repository is a transparent
failure-and-repair record, not a completed blind referee.**

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

## Version record

| Version | What it established | Current verdict |
|---|---|---|
| Local v1 auditor | Preserved false witnesses and a 1/3 score | Failed, useful negative result |
| Local repaired auditor | 3/3 on three author-built toy policies; byte-identical replay | Bounded local path-blind demonstration only |
| External v1 | Immutable public chronology and BLS-verifiable drand evidence | Failed hostile review |
| External v2 | Attempted blind registry, escrow, reveal, FINALIZE, and byte-pinning repairs; actual run 3/3 | **Frozen NO-GO** |

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

## Next gate: another administrator, not another process

Hosted-runner work is stopped. The same implementation on GitHub Actions would
add environment diversity while reproducing a relation already known to be
invalid. It would add neither independent implementation nor independent
custody, and GitHub Releases plus GitHub Actions are not provider-diverse.

Work resumes only if an independently administered co-custodian agrees to hold
the toy subjects and labels outside the author's pre-reveal access. The
bounded gate is in
[`V3_CUSTODY_GATE.md`](work/ceremony-zero-external-v2/V3_CUSTODY_GATE.md), and
the concrete request is
[`CO_CUSTODIAN_BRIEF.md`](work/ceremony-zero-external-v2/CO_CUSTODIAN_BRIEF.md).

If no custodian accepts, v2 remains the honest stopping point.

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
```

## License

MIT
