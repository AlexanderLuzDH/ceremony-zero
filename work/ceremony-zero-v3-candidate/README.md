# Ceremony Zero v3 pre-custody candidate

Status: `AUTHORITY_NONE_PRE_CUSTODY`

This directory contains one bounded candidate, not a v3 ceremony result. It
replaces v2's randomized corpus, beacon-selected phases, XOR escrow, and
executable Python subjects with a complete finite census, external withholding,
signed content-addressed records, and declarative subjects.

Run the conformance and hostile refusal suite from the repository root:

```console
python -B -m unittest -v work/ceremony-zero-v3-candidate/test_cz3.py
```

Rebuild and verify the deterministic known-answer fixture:

```console
python -B work/ceremony-zero-v3-candidate/make_test_fixture.py
```

The verifier deliberately requires the trust anchor and both externally pinned
roots as explicit inputs; it never promotes roots merely because they appear
inside a transcript. Exact TEST_ONLY replay values are recorded in
[`SOURCE_FREEZE.json`](SOURCE_FREEZE.json). For the frozen fixture:

```console
python -B work/ceremony-zero-v3-candidate/cz3_core.py work/ceremony-zero-v3-candidate/test_fixture --trust-anchor work/ceremony-zero-v3-candidate/test_fixture/TRUST_ANCHOR.json --prepare-root 9f014c71dc87cd93196666431951245384ee5717b65ccfcccc6eb49bb2324df2 --finalize-root 9867ec8b1523a1f02ccdc3bf5bf9a0051d5d13128370db559e9e8441944ab922
```

The included key, nonces, subjects, labels, and pinned roots are public,
deterministic `TEST_ONLY` material. A passing replay establishes internal
coherence only. It is not blind, independent, externally ordered, or evidence
about real subjects.
