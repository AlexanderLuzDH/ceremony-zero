# CEREMONY ZERO EXTERNAL V2 — frozen failed protocol

**Current verdict:**
`NO_GO_PRE_FINALIZE_LABEL_DISCLOSURE_REVEAL_ROUND_UNBOUND_AUDITOR_FALSE_WITNESSES_SUBJECT_AND_PHASE_BINDING_INCOMPLETE`

An external hostile review of v1 identified six protocol flaws. V2 verified
and accepted them and attempted the repairs recorded below. A fresh hostile
audit on 2026-08-27 falsified the claim that those repairs closed the protocol.
See [`V2_NO_GO.md`](V2_NO_GO.md) and the executable
[`test_v2_no_go.py`](test_v2_no_go.py). This document no longer grants v2 any
blind-referee authority.

## Flaws → Fixes

| # | v1 flaw | attempted v2 repair |
|---|---------|--------|
| 1 | Registry published subject kinds + triggers (the answers); audit read them | Registry contains ids and SHA-256s only; subjects are query-only modules whose bytes stay secret until reveal |
| 2 | Escrow XOR keystream from a public constant | Escrow key = SHA256(challenge_randomness), which exists only after PREPARE publication |
| 3 | Reveal beacon decorative (`reveal 00` → GO) | Reveal refuses without a locally BLS-verified reveal-round signature against the pinned chain key |
| 4 | Historical code identity unreconstructable | Runner's exact bytes hashed into registry AND published as a release asset; runner frozen before prepare |
| 5 | FINALIZE not enforced by reveal | Reveal asserts replica roots match FINALIZE.json, byte equality, before scoring |
| 6 | Runtime CRLF drift on Windows | All artifact writes binary or newline-pinned |

## Historical chronology

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

The actual run followed this chronology and scored 3/3. The chronology does
not repair the fact that public PREPARE/escrow artifacts disclosed the labels,
nor does it prove the implementation would reject alternate valid rounds or
substituted phase inputs.

## Boundaries and newly established failures

- Author/auditor separation is procedural: the author's local secret directory
  contains answers. Physical blindness requires a second custody domain.
- One provider carries the chronology; beacon signatures are now locally
  verified, but chain-key governance remains external to this machine.
- Subjects are toy policies. This is a referee demonstration, not an AI
  safety result.
- The auditor was intended to be sound within its declared bigram-trigger
  class, but valid seeds 53 and 61 produce false witnesses. That claim is
  withdrawn.
- The unsalted PREPARE label commitment is brute-forceable, and the escrow key
  is already public when escrow is released. Labels were not sealed until
  reveal.
- The reveal function accepts any valid drand round instead of enforcing the
  precommitted round.
- Hosted-runner replication is stopped. V3 may begin only after the independent
  custody gate in [`V3_CUSTODY_GATE.md`](V3_CUSTODY_GATE.md) is satisfied.
