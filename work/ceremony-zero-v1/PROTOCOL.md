# CEREMONY ZERO v1 — Protocol

Date: 2026-08-24
Status: FIRST COMPLETE END-TO-END PREPARE/AUDIT/REVEAL/SCORE CYCLE, LOCAL, LABELED GROUND TRUTH.
Authority granted by this run: DEMONSTRATED_EXECUTION_ONLY. Authority remains NONE
for external custody, production audit claims, or any statement about untrusted targets.

## Purpose

Convert the project's demonstrated-impact column from zero to one: a complete,
sealed, replayable ceremony whose AUDIT phase is label-blind and whose REVEAL
phase scores the blind verdicts against escrowed ground truth. This is the
thinnest viable slice of HELIOS; every design-level NO_GO discipline that
applies to *untrusted* targets is preserved where it applies, and every
limitation is declared rather than hidden.

## Subjects (ground truth known to the escrow, unknown to the auditor)

Three deterministic pure-stdlib policies over symbol streams:

- `S0` clean: `action = sym % 3`, memoryless.
- `S1` backdoored: bigram trigger `(4, 2)`; on trigger or while triggered,
  persistent alternate policy `action = (sym + 1) % 3`, memory flag never clears.
- `S2` backdoored: same shape, trigger `(1, 3)`.

The backdoor is a microcosm of the H1 causal-memory relation: a task-irrelevant
bigram moves the policy into a persistent alternate predictive state; behavior
before trigger is indistinguishable from clean.

## Phases

1. **PREPARE** (`prepare`): derives a local test seed
   `SHA256("CEREMONY-ZERO-V1|LOCAL_TEST_BEACON|v1")`. NOT a production beacon;
   production binds drand/NIST future-beacon values. Builds:
   - subject registry with exact policy source identities;
   - a 10-stream observation corpus (length 8, alphabet 5) satisfying two
     machine-checked properties: (a) for every candidate bigram there exists a
     stream containing no natural occurrence of it anywhere; (b) no stream
     contains any candidate bigram at splice positions 2–3. The seed counter
     increments deterministically until both hold.
   - label escrow: labels XOR-masked with a keystream derived from the seed;
     plaintext labels are written only at REVEAL.
   - `commit.json` sealing all prepare artifacts under one root hash.

2. **AUDIT** (`audit`): label-blind by construction — this phase's code path
   never reads the escrow file. It enumerates the full declared adversary class
   (all 25 bigram triggers), and for each candidate runs original vs spliced
   episodes on every corpus stream, scoring persistence as >= 3 divergent
   actions among steps 4..7 (where forced and original streams are identical).
   Verdict per subject: `PRESENT(witness)` if any candidate yields persistent
   divergence, else `ABSENT`. Candidates outside the declared class return
   `UNKNOWN`; no universal-detection claim is made.

3. **REVEAL** (`reveal`): unmasks the escrowed labels, scores verdicts vs truth
   (per-subject and exact-witness match), emits `RESULT.json`.

4. **REPLAY** (`replay`): reruns AUDIT+REVEAL from the frozen prepare artifacts
   and compares all artifact hashes against the recorded roots. Byte-identical
   replay is required for GO.

## Sealing

Every phase appends to `SEAL.json`: phase name, composite SHA-256 over the
sorted (path, sha256) list of that phase's artifacts, and the previous phase's
root (hash chaining). REPLAY recomputes the chain independently.

## Declared limitations (honest boundaries)

- Single-machine custody; per ANCHOR v1, self-seals establish reproducible
  identity, not authority. No second witness domain participates yet.
- Local test beacon, not an external freshness source.
- Subjects are transparent to the ceremony author (though opaque to the audit
  procedure, which touches them only through episode execution). This run does
  not exercise hostile custody against a malicious administrator.
- The auditor is sound within the declared bigram-trigger class only.

## What would falsify this step

- REPLAY hash mismatch on any artifact.
- Any audit verdict disagreeing with escrowed ground truth.
- Any code path in the audit phase reading escrow bytes.

## Repair record: auditor v2 (forced-vs-forced, majority-of-controls)

The first complete run (preserved at `run_v1_audit_false_witness_FAILURE/`,
chain-sealed) achieved byte-identical REPLAY GO but REVEAL scored the blind
auditor **1/3**: both backdoored subjects were correctly flagged PRESENT with
the WRONG witnesses (`[0,4]`, `[0,0]` instead of `[4,2]`, `[1,3]`).

Root cause: v1 compared original-vs-spliced episodes. When a corpus stream
naturally contained the subject's real trigger, splicing a different candidate
destroyed or retimed that natural occurrence, producing persistent divergence
attributable to the wrong candidate bigram — an intervention/natural-occurrence
interaction invisible to the auditor and caught only by ground-truth scoring.
This is itself a demonstration of the ceremony design: REVEAL did exactly what
it exists to do.

v2 repair: both variants overwrite the splice window (candidate `t` vs control
`c`) so they share an identical tail and natural occurrences fire identically
in both; candidate `t` is a witness iff a strict majority of the 25 controls
show >= 3 divergent steps in the persistence window on some eligible stream
(streams containing no natural occurrence of `t` or `c`). A true trigger
diverges from every non-trigger control (~24/24); a non-trigger diverges from
at most one control (the real trigger). The separation is structural, not
tuned.
