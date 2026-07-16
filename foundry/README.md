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
maintenance/ownership plan, and exit-gate status (met vs deferred human criteria).
