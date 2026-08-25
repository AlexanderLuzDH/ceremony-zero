# CEREMONY ZERO EXTERNAL V2 — Protocol (post hostile review)

An external hostile review of v1 identified six protocol flaws. All six were
verified, accepted, and repaired in this version. This document supersedes
v1's PROTOCOL.md disclosures.

## Flaws → Fixes

| # | v1 flaw | v2 fix |
|---|---------|--------|
| 1 | Registry published subject kinds + triggers (the answers); audit read them | Registry contains ids and SHA-256s only; subjects are query-only modules whose bytes stay secret until reveal |
| 2 | Escrow XOR keystream from a public constant | Escrow key = SHA256(challenge_randomness), which exists only after PREPARE publication |
| 3 | Reveal beacon decorative (`reveal 00` → GO) | Reveal refuses without a locally BLS-verified reveal-round signature against the pinned chain key |
| 4 | Historical code identity unreconstructable | Runner's exact bytes hashed into registry AND published as a release asset; runner frozen before prepare |
| 5 | FINALIZE not enforced by reveal | Reveal asserts replica roots match FINALIZE.json, byte equality, before scoring |
| 6 | Runtime CRLF drift on Windows | All artifact writes binary or newline-pinned |

## Chronology

1. PREPARE release: leak-free registry + exact runner bytes. Labels committed
   only as SHA-256. Reveal round pre-committed as challenge_round + 12.
2. Challenge drand round (> publication time) derives the corpus.
3. ESCROW release: labels masked with the challenge-derived key.
4. Blind dual-process audits (byte-equality required) → FINALIZE release.
5. At the pre-committed reveal round: signature BLS-verified locally,
   FINALIZE enforced, escrow unmasked with challenge randomness, label
   commitment checked, verdicts scored.
6. RESULT release publishes verdicts, plaintext labels, and the previously
   secret subject modules so anyone can replay everything.

## Honest boundaries (still true)

- Author/auditor separation is procedural: the author's local secret directory
  contains answers. Physical blindness requires a second custody domain.
- One provider carries the chronology; beacon signatures are now locally
  verified, but chain-key governance remains external to this machine.
- Subjects are toy policies. This is a referee demonstration, not an AI
  safety result.
- The auditor is sound only within its declared bigram-trigger class.
