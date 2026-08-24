# CEREMONY ZERO EXTERNAL v1 — Protocol

Date: 2026-08-24
Goal: the same ceremony shape as Ceremony Zero, but with an externally
ordered chronology — PREPARE committed to an immutable public release
BEFORE a drand challenge round, blind dual-process AUDIT, FINALIZE release
BEFORE a second reveal round. This is the gate between "local demonstration"
and "externally witnessed fact."

## Chronology (each step must complete before the next)

1. PREPARE package built locally: subject registry (fixed subjects,
   parameters, auditor design, exact code SHA-256) plus XOR-masked label
   escrow. The corpus derivation seed is deliberately OPEN — it comes only
   from post-publication beacon randomness.
2. PREPARE published as an immutable GitHub release asset on
   `AlexanderLuzDH/perfect-digital-referee-custody` (same repo and release
   regime as HELIOS v5). Publication time = GitHub's timestamp.
3. A drand round whose beacon time is strictly AFTER publication provides
   challenge randomness; corpus streams are derived deterministically from
   it (with a disclosed counter bump if the stream-quality predicate fails).
4. Blind AUDIT runs twice in separate interpreter processes
   (`python -B`, `python -B -I -S`). Byte equality of verdicts required.
5. FINALIZE record (both replica roots, verdict summary) published as a
   second immutable release BEFORE any reveal information exists.
6. A second drand round strictly after FINALIZE publication provides reveal
   randomness. Labels are then unmasked and scored.

## Honest boundaries (disclosed)

- Dual execution is same-implementation, two isolated processes: this is
  determinism evidence, not C4 implementation diversity. No hosted-runner
  replica in v1; that is the next repair if this gate passes.
- drand values are fetched over TLS without local BLS verification;
  chronology rests on GitHub timestamps + drand round times + TLS, exactly
  like HELIOS v5's withheld-BLS disclosure.
- Single-machine custody for all local steps; per ANCHOR v1, no authority
  against a hostile administrator is claimed.
- Beacon choice binds only the corpus in v1 (subjects and labels were fixed
  at prepare). Widening beacon scope is future work.

## Falsification

Any of: audit replicas disagreeing; FINALIZE published after reveal-round
time; verdicts disagreeing with escrowed truth; replay mismatch.
