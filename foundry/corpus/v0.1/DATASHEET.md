# Foundry Corpus Datasheet — v0.1 (sample)

## Motivation

Provide a public, provenance-tracked corpus of verification-aware tool-use
episodes for mathematical AI evaluation and diagnosis.

## Composition

Episodes are built from:

- committed offline evidence under `evidence/examples/`;
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
| Q2_formally_verified | replayable committed evidence |
| Q3_semantically_reviewed | human semantic review (none auto-assigned) |
| Q4_library_grade | library-integrated (none auto-assigned) |

## Contamination controls

- Immutable `train` / `eval` / `held_out` splits in `splits.json`.
- Content digests for duplicate detection.
- Synthetic negatives labeled and excluded from eval contamination.
- Flags for results already present in public libraries (default false for sample).

## Licensing

Apache-2.0 for MathEvidence-authored sample content. Solver artifact
redistribution rights must be reviewed before including proprietary backends'
raw outputs in future releases.

## Intended uses

- Verification-aware tool-selection training and evaluation.
- Failure diagnosis (negative episodes).
- System benchmarking (not capability promotion alone).

## Out of scope / known limitations

- Not a claim of live frontier acceleration.
- Sample is small and algebra/calculus-skewed.
- Q3/Q4 require human review queues not closed by this release.

## Maintenance

See `docs/foundry/maintenance-ownership.md`.
