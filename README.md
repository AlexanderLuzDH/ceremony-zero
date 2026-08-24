# Ceremony Zero

**A transparent, replayable referee for blind AI-style audits — demonstrated
end-to-end on labeled ground truth, witnessed in public.**

Ceremony Zero is a minimal but *complete* implementation of a trust question
that matters more every year:

> Can a referee judge whether a system has hidden behavior — **before anyone
> knows the right answer** — and prove afterward that it could not have
> cheated?

This repository contains the full working answer: the ceremony code, the
sealed run artifacts, an externally ordered chronology (GitHub immutable
releases + drand beacon rounds), and local BLS verification of that beacon.
Everything here is small enough to read in an afternoon and attack before
dinner.

## The three moves

1. **PREPARE** — subjects are built; ground-truth labels are XOR-masked into
   escrow. The audit corpus is *deliberately left open*, to be derived only
   from future public randomness.
2. **AUDIT** — a label-blind auditor exhaustively enumerates a declared
   adversary class (all 25 bigram triggers) using forced-vs-forced
   interventions with a majority-of-controls rule, and commits its verdicts.
3. **REVEAL** — only after verdicts are frozen does a second public random
   round arrive; labels are unmasked and the auditor is scored against truth.

## What happened when we ran it

- The first auditor **failed** — ground-truth scoring caught it producing
  false witnesses via an intervention/natural-occurrence interaction. The
  failure is preserved, not hidden:
  [`run_v1_audit_false_witness_FAILURE/`](work/ceremony-zero-v1/run_v1_audit_false_witness_FAILURE)
- The repaired auditor scored **3/3 with exact witnesses**, twice,
  byte-identically, including a test where we destroyed the escrow and proved
  the auditor's output didn't change.
- Then we ran the whole thing again under a **public chronology** no single
  party controls.

## Public receipts (the externally witnessed run)

| Time (UTC) | Event | Receipt |
|---|---|---|
| 2026-08-24T11:04:49Z | PREPARE committed, labels masked | [release](https://github.com/AlexanderLuzDH/perfect-digital-referee-custody/releases/tag/ceremony-zero-ext-v1-prepare-9d412ae4ab0f7806e5b24748f2f92023f45b75df11351cf261693077c31892b4) |
| +191s | drand challenge round `6404621` derives the corpus | randomness verified below |
| (blind audits ×2, byte-equal) | verdicts frozen | |
| 2026-08-24T11:09:46Z | FINALIZE released — answers still sealed | [release](https://github.com/AlexanderLuzDH/perfect-digital-referee-custody/releases/tag/ceremony-zero-ext-v1-finalize-6cd2d41502c2ae5a6d7353fbe376e928f9b6d86ef35c5045e9ae538345fa0402) |
| +74s | drand reveal round `6404627` | randomness verified below |
| 2026-08-24T11:11:22Z | RESULT released: **3/3, CEREMONY_GO=TRUE** | [release](https://github.com/AlexanderLuzDH/perfect-digital-referee-custody/releases/tag/ceremony-zero-ext-v1-result-0a036845775b70fe39c8fac2c72bde5be287ae95288261218e44d9372e9487c8) |

**Local BLS verification: PASS.** Both ceremony rounds were verified against
drand league chain `8990e7a9…b2ce`'s pinned group public key using py_ecc
(scheme `pedersen-bls-chained`, digest = SHA256(prevSig ‖ round_BE64), DST
`…SSWU_RO_NUL_`). See `verify_bls.py` → `run/bls_verification.json`.
The entropy that chose the corpus and timed the reveal is a cryptographically
verified threshold signature — not "some API said so."

## Attack it (please)

This protocol is worth exactly what survives hostile scrutiny. Good places to
start:

- **Replay**: re-run `ext_ceremony.py` phases from the published assets and
  check every root matches.
- **Forge**: produce any artifact set that passes verification but encodes
  different verdicts/labels.
- **Blindness breakage**: find any input path by which the audit phase can
  learn escrowed labels.
- **Auditor unsoundness**: construct a subject within the declared bigram class
  that the majority-of-controls census misjudges — or show the declared class
  itself is degenerate.
- **Chronology**: find a way to know the challenge randomness before the
  PREPARE release timestamp.

Open an issue with anything you find. Negative results documented honestly are
welcome too.

## Honest boundaries (read before being impressed)

- Subjects are tiny deterministic policies — this demonstrates a *referee
  design*, not an AI safety result.
- Single-machine custody for all local steps. Per our own ANCHOR theorem,
  self-seals establish reproducible identity, not authority. A second custody
  domain is the next milestone.
- Dual-process execution is determinism evidence, not independent
  implementation diversity.
- The auditor is sound only within its declared adversary class; outside it,
  the correct answer is UNKNOWN.
- One provider (GitHub) carries the chronology; one relay served the beacon
  bytes (though their BLS signatures now verify locally).

## Repository layout

```
work/ceremony-zero-v1/            local Ceremony Zero (v1 failure + v2 pass)
  PROTOCOL.md                     protocol + repair record
  ceremony.py                     prepare/audit/reveal/replay implementation
  run/                            sealed passing artifacts
  run_v1_audit_false_witness_FAILURE/   preserved negative result

work/ceremony-zero-external-v1/   externally ordered chronology
  PROTOCOL.md                     chronology + honest boundaries
  ext_ceremony.py                 make-prepare / derive-corpus / audit /
                                  make-finalize / reveal
  verify_bls.py                   local BLS verification of drand rounds
  run/                            all artifacts incl. bls_verification.json
```

Requires Python 3.11+ (`pip install py_ecc` only for `verify_bls.py`; the
ceremonies themselves are pure stdlib).

## Why "Zero"?

Because everyone has to start somewhere — and because the number of times
this exact complete sequence had been publicly executed, sealed, and scored
against ground truth was zero.

## License

MIT
