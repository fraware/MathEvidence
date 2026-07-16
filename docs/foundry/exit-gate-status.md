# Milestone 6 exit-gate status

Tracked against `docs/DELIVERY_ROADMAP.md` Milestone 6 and Product 08 acceptance
criteria. Engineering artifacts can be met in-repo; research / funding / live
collaboration criteria cannot be closed by code alone.

**Honesty:** Do not claim live frontier acceleration, funding secured, or
maintainer sign-off. Tool-selection lift below is **reference vs naive baseline**
on the harness — not a trained-model held-out uplift.

## Deliverables

| Deliverable | Status | Artifact |
| --- | --- | --- |
| Public certified tool-use corpus | **Met (sample)** | `foundry/corpus/v0.1/` (12 episodes) |
| Provenance, quality tiers, contamination controls | **Met** | corpus schemas + `contamination.json` / `splits.json` / datasheet |
| Verification-aware tool-selection benchmark | **Met (harness)** | `benchmarks/tool_selection/` + `scripts/run_tool_selection_benchmark.py` |
| Baseline vs reference metrics | **Met (engineering)** | `scripts/metrics/foundry_tool_selection.py` — measured lift is harness-only |
| Corpus build-quality metrics | **Met (engineering)** | `scripts/metrics/foundry_corpus_quality.py` |
| Frontier collaborations scaffolding | **Met (notes)** | `docs/foundry/frontier-collaborations.md` |
| Measured library contribution tracking | **Met (script + empty ledger)** | `scripts/metrics/track_contributions.py`; `docs/foundry/contributions/` (0 records) |
| Maintenance funding / ownership plan | **Met (plan doc)** | `docs/foundry/maintenance-ownership.md` — funding **not secured** |
| Pipelines from evidence/episodes without acceptance influence | **Met** | `foundry/pipelines/` |
| §19 instrumentation | **Met (engineering)** | `scripts/metrics/` (`verified_coverage`, `open_replay_rate`, `semantic_defect_rate`) |

## Exit criteria

| Criterion | Status | Notes |
| --- | --- | --- |
| Data improves held-out verified tool use | **OPEN (research)** | Reference policy accuracy measured; naive baseline comparison recorded via `just foundry-metrics`. **No trained selector uplift claimed.** |
| ≥1 frontier program materially accelerated | **OPEN (human / external)** | Collaboration notes only; no live acceleration claimed |
| Maintenance funding and ownership established | **OPEN / partial** | Ownership map documented; funding **not secured** |

## Product 08 acceptance criteria

| Criterion | Status |
| --- | --- |
| Every Q2+ episode replays (committed evidence path) | **Met for sample Q2** via existing offline-replay CI on source bundles |
| Quality tiers independently auditable | **Met** (schema + manifest tier composition + `foundry_corpus_quality`) |
| Negative episodes improve failure diagnosis on held-out tasks | **Partial** — synthetic negatives + benchmark harness present; empirical model uplift OPEN |
| Dataset use improves verified tool selection, not mere call frequency | **OPEN (research)** — scoring metric + baseline/reference measurement exist; trained uplift not claimed |
| Releases include datasheets, licenses, benchmark exclusions, known biases | **Met** for v0.1 sample |

## How to measure (engineering)

```text
just foundry-metrics
just metrics
```

## Hard invariant

All Foundry corpus and capture artifacts set `acceptanceInfluence: false` and
MUST NOT be consulted by Lean checkers or theorem acceptance paths.
