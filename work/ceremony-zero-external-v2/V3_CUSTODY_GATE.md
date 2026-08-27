# Ceremony Zero v3 — custody-first resume gate

Status: **PRE-CUSTODY CANDIDATE FROZEN NO-GO; NO REPAIR, EXECUTION, OR
EVIDENCE AUTHORITY**

## 2026-08-27 narrow exception

The user explicitly authorized one separate, authority-`NONE` engineering
cycle before a custodian accepts. It may produce only frozen candidate bytes,
synthetic conformance fixtures, and hostile refusal tests. It may not run a v3
ceremony, consume held-out evidence, claim blindness, add hosted infrastructure,
or touch real subjects. The separate charter is
[`../ceremony-zero-v3-candidate/CHARTER.md`](../ceremony-zero-v3-candidate/CHARTER.md).

This exception also removes inherited machinery that has no decision role in
the exhaustive finite design: no randomized corpus means no challenge beacon;
external withholding means no escrow; and no selectable reveal event means no
reveal beacon. A future custodied execution must instead externally pin the
exact PREPARE and FINALIZE record roots before proceeding.

The exception has now been consumed. The frozen candidate failed its
post-freeze hostile review on nonce-length enforcement, total malformed-JSON
refusal, and duplicate-key/canonical-byte binding. See
[`../ceremony-zero-v3-candidate/FREEZE.md`](../ceremony-zero-v3-candidate/FREEZE.md).
Per its charter, those bytes are preserved and no repair generation is
authorized without a new explicit user decision.

Purpose: define the smallest external event that justifies another protocol
implementation.

## Real function

Demonstrate that a fixed auditor evaluates independently generated subjects
and ground truth without the author learning labels early, selecting a
favorable challenge, substituting subjects or verdicts, or choosing a reveal
event after seeing results.

## Resume condition

Do not execute v3 or grant evidence authority until a named co-custodian,
outside the author's administrative domain, agrees to all of the following:

1. generate or receive the held-out toy subjects and ground truth only after
   the auditor and protocol are frozen;
2. keep subject semantics, labels, commitment nonce, and any escrow key outside
   the author's pre-reveal access;
3. execute the frozen auditor in the custodian's domain, or expose a bounded
   black-box query interface that does not disclose subject code;
4. publish PREPARE, FINALIZE, and REVEAL receipts from that domain; and
5. reveal the subjects and labels after FINALIZE so strangers can reproduce
   and attack the result.

If no custodian accepts, the project stops at the v2 NO-GO. That is a valid
closure outcome.

## Minimum v3 protocol obligations

A future v3 design must make these properties executable, not narrative:

- **Hiding commitment:** the custodian holds the labels and a 256-bit random
  nonce until reveal. Never use public challenge randomness as a label-
  encryption key. Include a brute-force resistance negative test.
- **No selectable challenge:** exhaust the complete finite toy class and fixed
  query domain. If a future design reintroduces sampling, the challenge source
  and exact selection rule must be separately reauthorized and bound.
- **Externally pinned chronology:** audit only after the exact PREPARE root is
  externally pinned, and reveal only after the exact FINALIZE root is
  externally pinned. The candidate verifier consumes those roots as external
  trust inputs; it does not treat transcript-supplied receipts as authority.
- **Complete phase state machine:** each phase root binds the prior root, exact
  code, parameters, subjects, challenge evidence, verdicts, and publication
  receipt. RESULT carries the complete chain.
- **Subject integrity:** verify committed subject bytes or authenticated
  black-box identity before every audit query.
- **Auditor soundness:** for the finite toy class, exhaustively test every clean
  policy and every declared trigger. Random seed sampling is not a substitute
  for a finite-class soundness gate. Ambiguity must return `UNKNOWN`, never a
  guessed witness.
- **Independent review:** freeze v3 bytes and obtain a fresh hostile review
  before consuming the custodian's held-out evidence.

## What does not satisfy the gate

- two processes on one machine;
- the same implementation on GitHub Actions;
- a second account controlled by the author;
- public labels encrypted with a public value;
- post-reveal reproduction; or
- an AI review commissioned and selected solely by the author.

Execution-environment or provider diversity may be added after these
obligations pass. It cannot replace independent custody or protocol soundness.

## Bounded next action

Stop. The single authority-`NONE` candidate did not survive hostile review.
Do not send it as runnable code or begin another implementation cycle. Any
repair requires a new explicit user decision; any later evidence-producing run
still requires an independent custodian.
