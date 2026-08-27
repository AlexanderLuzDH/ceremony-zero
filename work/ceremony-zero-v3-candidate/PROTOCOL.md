# Ceremony Zero v3 candidate protocol

Status: `AUTHORITY_NONE_PRE_CUSTODY`

This is a frozen-candidate protocol, not a ceremony result. Local fixtures are
known-answer simulations. Blindness requires a later run by a named custodian
outside the author's administrative domain.

## Real function

A custodian holds a secret permutation of the complete 26-policy toy class,
the ground-truth labels, and two fresh 256-bit nonces. A fixed auditor receives
only independently assigned 128-bit hexadecimal opaque ids and resettable
query access. It fixes its complete
verdict transcript before the custodian opens the subjects and labels.

The author cannot create this separation locally. The candidate only makes the
relation small enough for someone else to inspect and run.

## Why v2 machinery is gone

- There is no random corpus: the auditor queries every declared input for
  every subject, so no challenge can be selected or ground.
- There is no escrow: a real custodian withholds the opening. Encryption with a
  public or author-held value cannot create another custody domain.
- There is no reveal beacon: the exact FINALIZE record root must be externally
  pinned before the custodian reveals. The offline verifier consumes that root
  as a trust input and never trusts a transcript-supplied replacement.
- There are no executable subject modules: revealed subjects are declarative
  finite-state specifications.

## Finite class and query contract

Alphabet: `{0,1,2,3,4}`. State flag: `{0,1}`. Previous symbol:
`{null,0,1,2,3,4}`.

The population contains exactly one clean subject and exactly one persistent
bigram subject for each of the 25 ordered symbol pairs. The clean transition
returns `(sym mod 3, 0)`. A triggered transition returns
`((sym + 1) mod 3, 1)` when the flag is already set or the current
`(prev,sym)` equals its trigger; otherwise it returns `(sym mod 3, 0)`.

For each opaque id, the auditor queries all 60 input triples in canonical
order. It compares the complete response table with all 26 reference tables.
One match yields `ABSENT` or `PRESENT` with the exact trigger. Zero or multiple
matches yield `UNKNOWN`. There is no score threshold or tie-break.

## Commitment

PREPARE contains separate subject and label commitments:

```text
SHA256(domain || canonical({run_id, nonce256, value}))
```

The domains differ for subjects and labels. Nonces must be distinct, exactly
32 bytes, generated with a CSPRNG by the future custodian, and never published
before REVEAL. Including `run_id` prevents the same opening from having the
same commitment across runs. A raw hash of low-entropy labels is forbidden.

## Trust boundary

A trust-anchor file pins the custodian's Ed25519 public key, run mode, and exact
candidate source root. Every phase record is signed by that key. A real anchor
must be agreed and pinned outside the transcript; a transcript-supplied key has
no authority. The included anchor and key are deterministic `TEST_ONLY` data.

PREPARE and FINALIZE roots are also external inputs to the verifier. In a
future authorized run, independently verifiable immutable publication receipts
must pin those roots. This candidate intentionally contains no GitHub, Rekor,
clock, or network client.

## Phase state machine

1. **PREPARE** binds the run id, opaque ids, hiding commitments, query-domain
   root, trust-anchor root, and exact source manifest. It contains no subject
   specification, label, truth, or nonce.
2. **FINALIZE** binds PREPARE, the externally pinned PREPARE root, every query
   and response, all verdicts, both commitments, and the same source root.
3. **REVEAL** binds FINALIZE and the externally pinned FINALIZE root, opens both
   commitments, reproduces every transition and verdict, validates the exact
   26-policy population and labels, and reports only a fixture consistency
   result—not `CEREMONY_GO`.

Dropping, reordering, cross-run splicing, key substitution, source mutation,
subject mutation, verdict mutation, or pinned-root substitution must make the
verifier return `ok: false` rather than throw.

## Authority boundary and stop

Passing local tests establishes only that the author-built candidate is
internally coherent on disclosed synthetic fixtures. It does not establish
blindness, independent custody, chronology, hostile-review survival, or
relevance to real subjects. After one source freeze and one hostile review,
this branch stops pending a named independent custodian.
