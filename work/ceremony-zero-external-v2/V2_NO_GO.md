# Ceremony Zero External v2 — frozen NO-GO

Date: 2026-08-27

Evaluated commit: `0103d9c613cb46bcb9602a41fc1c93a8509005bd`

Frozen runner SHA-256:
`649f070c08e44bfbdd852908e782e283b2c070db4887cf4d0542cf0e82591acd`

## Verdict

`NO_GO_PRE_FINALIZE_LABEL_DISCLOSURE_REVEAL_ROUND_UNBOUND_AUDITOR_FALSE_WITNESSES_SUBJECT_AND_PHASE_BINDING_INCOMPLETE`

The v2 chronology and 3/3 result remain preserved historical facts. They do
not establish that labels were secret until reveal, that the precommitted
reveal round was machine-enforced, or that the auditor was sound within the
declared bigram class. No v2 runner or run artifact was edited during this
closure.

## Reproduced counterexamples

1. **PREPARE discloses the low-entropy labels.** The unsalted
   `labels_sha256` commitment can be searched over the 26 declared outcomes
   for each of three subjects. The exact ground truth is recovered on guess
   608.
2. **The escrow is publicly decryptable before FINALIZE.** Its XOR keystream
   is derived only from challenge randomness that is already public when the
   escrow is released. No reveal signature is needed.
3. **The reveal round is not bound.** The runner records the rule
   `challenge_round + 12`, but `cmd_reveal` accepts any valid drand round. The
   valid challenge-round signature for round `6407783` passes the reveal BLS
   verifier even though the committed reveal round is `6407795`.
4. **The repaired auditor still returns false witnesses.** On valid
   deterministic challenge seeds 53 and 61, S1's true witness `[4,2]` is
   reported as `[2,4]` and `[2,1]` respectively. A 100-seed diagnostic panel
   recovered 98/100 exact witnesses.
5. **Committed subject identity is not enforced.** `cmd_audit` imports and
   executes subject modules without comparing their bytes with the hashes in
   `prepare/registry.json`.
6. **The phase chain is incomplete.** FINALIZE binds two local verdict files;
   reveal checks a mutable local FINALIZE. RESULT does not carry the complete
   PREPARE, challenge, escrow, code, subject, and published-FINALIZE roots.

## Reproduce

From the repository root, with Python 3.11+ and `py_ecc>=8.0.0` installed:

```console
python -B -m unittest -v work/ceremony-zero-external-v2/test_v2_no_go.py
```

The eight tests are expected to pass because each test reproduces a v2 failure.
They are hostile closure evidence, not v3 conformance tests.

## Claims withdrawn

Do not describe v2 as:

- keeping the answers secret until reveal;
- closing all six prior hostile-review findings;
- enforcing the precommitted reveal round;
- sound within the declared bigram-trigger class;
- surviving hostile review; or
- ready for a hosted replica.

The bounded positive claim is narrower: v2 is a public, replayable historical
commit/finalize/reveal transcript whose actual run used BLS-verified drand
values and scored 3/3 on three author-generated toy policies. It is not an
independently blind referee.

## Disposition

Hosted-runner work is stopped. Reproducing a known-invalid relation in another
environment cannot add semantic authority.

Work may resume only under the exit conditions in
[`V3_CUSTODY_GATE.md`](V3_CUSTODY_GATE.md), beginning with a genuinely
independent custodian rather than another self-administered execution layer.
