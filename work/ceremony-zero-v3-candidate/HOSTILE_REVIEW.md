# Ceremony Zero v3 candidate — post-freeze hostile review

Date: 2026-08-27

Reviewer: internally commissioned AI challenger. This was **not** an
independent external review and grants no authority.

Reviewed source inventory root:
`918ccae34925b228c287e9a27981bd0a7dc6a36e1c73aaa2bc0978cb8986ea9c`

No declared frozen file was edited during or after this review.

## Verdict

`FROZEN_V3_CANDIDATE_NO_GO`

All 21 author tests pass, and the finite classifier itself is sound over the
declared 26 policies and 60 inputs. The frozen candidate nevertheless has
three fatal verifier defects.

## Fatal findings

### 1. The claimed 256-bit nonce check accepts zero- and one-byte values

`require_hex` checks the string length and then calls `bytes.fromhex`, which
ignores ASCII whitespace. Sixty-four spaces are accepted but decode to zero
bytes; 62 spaces followed by `00` decode to one byte.

A complete PREPARE -> FINALIZE -> REVEAL transcript was rebuilt and re-signed
with a zero-byte subject nonce and one-byte label nonce. The frozen verifier
returned `ok: true`. That violates the strict 32-byte hiding obligation and can
reopen cheap commitment search.

### 2. The public CLI is not total

`verify_transcript` catches semantic verification errors, but the command-line
entry point parses JSON before entering it. Malformed JSON therefore produces
an uncaught traceback instead of the promised deterministic `ok: false`.

### 3. Published JSON bytes are not unambiguously bound

The parser accepts duplicate JSON keys, while record roots and signatures are
computed over the collapsed Python object. Prepending a conflicting duplicate
`payload_sha256` changed the PREPARE file bytes without changing the parsed
object, signature, external pin, or reported phase root. The command-line
verifier returned `ok: true`.

This creates cross-parser ambiguity: a first-key-wins consumer can see a
different record from the frozen verifier's last-key-wins interpretation.

## Nonfatal findings and boundaries

- Every one of the 12 declared source/fixture files matches its recorded byte
  count and SHA-256. The inventory root reproduces with PowerShell-style
  case-insensitive path sorting, but the freeze record did not state that
  collation rule.
- A stale ignored `__pycache__` file existed locally and was omitted from the
  explicit 12-file inventory. It is not a tracked source file, but the
  inventory exclusion wording was incomplete.
- A coherent replacement of the trust anchor, key, records, and caller pins is
  accepted. That is an admitted external-authentication boundary, not authority
  created by this checker.
- The source root omits the Python runtime and exact dependency closure.
- Random opaque-id generation, CSPRNG use, lack of covert label encoding, and
  genuine namespace separation remain future-custodian obligations.
- The only included FINALIZE builder is TEST_ONLY and sees declarative subject
  specifications. No real black-box custody adapter exists.

## What held

- The 26 reference transition tables are unique and all declared subjects are
  classified exactly over the complete 60-input query domain.
- Out-of-class tables return `UNKNOWN`.
- Parsed-object phase chaining, wrong-pin refusal, cross-run splice refusal,
  source checks, commitment opening, declarative replay, and authority-`NONE`
  wording held under attack.
- PREPARE and FINALIZE do not contain opening or ground-truth fields on the
  intended path.

## Disposition

Preserve the candidate as NO-GO. The charter forbids a repair generation after
this review without a new explicit user decision.
