# Foundry Corpus Datasheet — v0.1

## Motivation

Provide a public, provenance-tracked corpus of verification-aware tool-use
episodes for mathematical AI evaluation and diagnosis.

## Composition

Episodes are built from:

- committed offline evidence under `evidence/examples/`;
- conformance offline bundles under `evidence/conformance/` (request+certificate);
- FiniteGraph certified refutations under `evidence/conjecture/finite_graph/`;
- optional Foundry capture-hook records under `foundry/episodes/`;
- labeled synthetic negatives for tool-selection failure modes.

## Hard invariant

`acceptanceInfluence` is always `false`. This corpus MUST NEVER influence Lean
theorem acceptance, checker results, or `ResultStatus`.

## Quality tiers

| Tier | Meaning |
| --- | --- |
| Q0_raw | unreviewed |
| Q1_schema_valid | schema-valid / metadata complete |
| Q2_formally_verified | replayable evidence / certified rejection |
| Q3_semantically_reviewed | human semantic review (not auto-assigned) |
| Q4_library_grade | library-integrated (not auto-assigned) |

Q3 review-ready packets live in `review_queue/` with status
`awaiting_human_review`. They are **not** counted as Q3 until humans add
`humanReviewLabels`.

## Contamination controls

- Immutable `train` / `eval` / `held_out` splits by **source family** (not random).
- Content digests for duplicate detection.
- Synthetic negatives labeled and excluded from eval contamination.
- Flags for results already present in public libraries (default false).

## Licensing

Apache-2.0 for MathEvidence-authored content. Solver artifact redistribution
rights must be reviewed before including proprietary backends' raw outputs.

## Intended uses

- Verification-aware tool-selection training and evaluation.
- Failure diagnosis (negative episodes).
- System benchmarking (not capability promotion alone).

## Out of scope / known limitations

- Not a claim of live frontier acceleration.
- FiniteGraph precision metrics are campaign-local, not field-level.
- Q3/Q4 require human review; queue packets are unlabeled by design.
- Independent evaluation: `python scripts/evaluate_foundry_corpus.py`.

## Maintenance

See `docs/foundry/maintenance-ownership.md`.
