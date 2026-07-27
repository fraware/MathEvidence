# Foundry

Certified tool-use episode schemas, capture hooks, and corpus pipelines.

## Invariant

Training / corpus episodes **MUST NEVER** influence theorem acceptance, checker
results, or `ResultStatus`. Capture and pipelines run after orchestration
decisions and are audit-only (`acceptanceInfluence: false`).

## Layout

- `schema/training-episode.schema.json` — capture-hook episodes
- `schema/corpus-episode.schema.json` — public corpus episodes (provenance, tiers, contamination)
- `schema/corpus-release.schema.json` — release packaging + tier composition
- `capture.py` — write raw episodes under `foundry/episodes/` (gitignored)
- `pipelines/` — ingest evidence/captures, validate, dedupe, quality, split, package
- `corpus/v0.1/` — sample public corpus slice (committed)

## Capture

```python
from foundry.capture import capture_episode

capture_episode(kind="hypothesis_lattice", payload={...})
```

Or pass `captureEpisode: true` to Agent hypothesis/conjecture operations.

## Build / validate corpus

```text
python scripts/build_foundry_corpus.py
python scripts/validate_foundry_corpus.py
# or:
just foundry-corpus
just foundry-validate
```

## Tool-selection benchmark

```text
python scripts/run_tool_selection_benchmark.py
just tool-selection
```

## Docs

See `docs/foundry/` for frontier collaboration notes, contribution tracking,
and maintenance/ownership plan. Honest open exits: `docs/STATUS.md` and
`docs/security/KNOWN_TRUST_GAPS.md`.

## Quality tiers (ME-RV-080)

| Tier | Meaning |
| --- | --- |
| Q0_raw | unreviewed |
| Q1_schema_valid | schema-valid / metadata complete |
| Q1_checker_preview | checker/offline replay without Certification Record |
| Q2_formally_verified | Certification Record + theorem identity + environment lock |
| Q3_semantically_reviewed | human semantic review (not auto-assigned) |
| Q4_library_grade | library-integrated (not auto-assigned) |

The v0.1 sample corpus was reclassified: historical `Q2_formally_verified` without
Certification Records are `Q1_checker_preview`. Use family-normalized metrics
(`scripts/metrics/foundry_corpus_quality.py`); do not treat FiniteGraph volume as
independent-domain coverage. `sourceCommit: workspace` is forbidden on releases.
