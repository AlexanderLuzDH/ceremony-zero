# V2 failure-to-v3 disposition

Status: `AUTHORITY_NONE_PRE_CUSTODY`

| Frozen v2 failure | V3 candidate disposition | Enforced by |
|---|---|---|
| Unsalted, brute-forceable label hash | Separate domain-bound label commitment with run id and a strict 256-bit custodian nonce; PREPARE rejects openings | `test_nonce_hides_low_entropy_labels_and_is_strict`, schema verification |
| Publicly decryptable escrow | Escrow and encryption removed; a future custodian withholds labels and nonce | `test_prepare_and_finalize_contain_no_opening_or_ground_truth` |
| Alternate valid reveal round accepted | No challenge/reveal round exists because the audit is a complete finite census; FINALIZE's exact externally pinned root is the only reveal prerequisite | wrong-pin and complete-chain tests |
| Seeds 53 and 61 produce false witnesses | Seeds, corpora, votes, and tie-breaking removed; all 26 policies and all 60 interface inputs are exhausted | `test_complete_26_policy_population_classifies_exactly` |
| Substituted subject bytes execute | Arbitrary code removed; private declarative bundle must open PREPARE before the first query, and every revealed transition must replay FINALIZE | subject-commitment and reveal-substitution tests |
| FINALIZE binds only two verdict files | FINALIZE binds PREPARE, external PREPARE pin, source, commitments, full query transcript, verdicts, and audit root | `test_complete_phase_chain_is_carried_to_reveal` |
| RESULT omits upstream roots | REVEAL carries PREPARE and FINALIZE roots, both external pins, source root, commitments, opening, and exact replay result | schema and complete-chain tests |
| Mutable/local trust inputs can be substituted coherently | Custodian key and source root come from an external trust anchor; PREPARE and FINALIZE roots are explicit verifier inputs | key-, source-, cross-run-, and wrong-pin tests |

These are conformance properties of author-built bytes. They are not evidence
that an independent custodian actually withheld anything.
