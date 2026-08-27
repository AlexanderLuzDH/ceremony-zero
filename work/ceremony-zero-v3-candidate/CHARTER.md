# Ceremony Zero v3 pre-custody candidate charter

Date: 2026-08-27

Status: `AUTHORITY_NONE_PRE_CUSTODY`

## Operational target

Produce one small, frozen specification, exhaustive toy auditor, and offline
transcript verifier that a future independent custodian can inspect and later
execute without giving the author pre-FINALIZE access to subject identities,
ground truth, or the commitment nonce.

This cycle tests engineering coherence only. It cannot demonstrate blindness,
independent custody, public chronology, or institutional credibility.

## Method contract

- Preserve v1 and v2 bytes and their failures unchanged.
- Use synthetic known-answer fixtures only.
- Model subjects declaratively; never import or execute subject-provided code.
- Audit the complete finite population: one clean policy and all 25 persistent
  bigram triggers over alphabet size five.
- Exhaust the complete declared query interface; no seeds, sampling, majority
  vote, threshold, or guessed witness. Non-matches return `UNKNOWN`.
- Hide the complete subject/label bundle behind a domain-separated commitment
  containing a fresh 256-bit custodian nonce and run id.
- Bind exact source, PREPARE, FINALIZE, query transcript, reveal opening, and
  externally supplied pinned roots. Fail closed on any substitution.
- Label every local key, fixture, transcript, score, and freeze
  `AUTHORITY_NONE_PRE_CUSTODY` and `TEST_ONLY` where applicable.

## Authorized product

One protocol document, compact pure verifier/auditor, TEST_ONLY fixture
generator, exhaustive and hostile tests, exact source manifest, freeze record,
and one independent hostile review.

## Explicit exclusions

No v3 ceremony run; no live release chronology; no GitHub Actions, drand,
timelock or escrow encryption, Docker, sandbox, real model or checkpoint,
arbitrary Python subject, generalized custody service, second implementation,
or JANUS claim.

## Exit

Freeze once. If all obligations pass, terminate as
`FROZEN_PRE_CUSTODY_CANDIDATE_AUTHORITY_NONE_AWAITING_EXTERNAL_REVIEW_AND_CUSTODY`.
If a fatal flaw remains, preserve it as `FROZEN_V3_CANDIDATE_NO_GO`. No repair
generation is authorized after the hostile review without a new user decision.
