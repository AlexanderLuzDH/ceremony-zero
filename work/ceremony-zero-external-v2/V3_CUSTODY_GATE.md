# Ceremony Zero v3 — custody-first resume gate

Status: **NO IMPLEMENTATION AUTHORITY**

Purpose: define the smallest external event that justifies another protocol
implementation.

## Real function

Demonstrate that a fixed auditor evaluates independently generated subjects
and ground truth without the author learning labels early, selecting a
favorable challenge, substituting subjects or verdicts, or choosing a reveal
event after seeing results.

## Resume condition

Do not implement or run v3 until a named co-custodian, outside the author's
administrative domain, agrees to all of the following:

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
- **Exact challenge binding:** commit the chain identity and deterministic
  round-selection rule before fetching the beacon. Verify the challenge
  signature and `randomness = SHA256(signature)` before deriving any choice.
- **Exact reveal binding:** require the one precommitted reveal round, verify
  its signature and derived randomness, and prove that the published FINALIZE
  receipt predates that round. Any other valid drand round must be rejected.
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

Send [`CO_CUSTODIAN_BRIEF.md`](CO_CUSTODIAN_BRIEF.md) to prospective
custodians. No further ceremony infrastructure is authorized before one
accepts.
