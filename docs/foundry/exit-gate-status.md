# Milestone 6 exit-gate status

Tracked against `docs/DELIVERY_ROADMAP.md` Milestone 6 and Product 08 acceptance
criteria. Engineering artifacts can be met in-repo; research / funding / live
collaboration criteria cannot be closed by code alone.

## Deliverables

| Deliverable | Status | Artifact |
| --- | --- | --- |
| Public certified tool-use corpus | **Met (sample)** | `foundry/corpus/v0.1/` |
| Provenance, quality tiers, contamination controls | **Met** | corpus schemas + `contamination.json` / `splits.json` / datasheet |
| Verification-aware tool-selection benchmark | **Met (harness)** | `benchmarks/tool_selection/` |
| Frontier collaborations scaffolding | **Met (notes)** | `docs/foundry/frontier-collaborations.md` |
| Measured library contribution tracking | **Met (template)** | `docs/foundry/library-contribution-template.md` |
| Maintenance funding / ownership plan | **Met (plan doc)** | `docs/foundry/maintenance-ownership.md` |
| Pipelines from evidence/episodes without acceptance influence | **Met** | `foundry/pipelines/` |

## Exit criteria

| Criterion | Status | Notes |
| --- | --- | --- |
| Data improves held-out verified tool use | **Deferred (research)** | Benchmark + reference policy exist; model improvement vs baseline not measured with a trained selector in this milestone |
| ≥1 frontier program materially accelerated | **Deferred (human / external)** | Collaboration notes only; no live acceleration claimed |
| Maintenance funding and ownership established | **Partial / deferred** | Ownership map documented; funding **not secured** |

## Product 08 acceptance criteria

| Criterion | Status |
| --- | --- |
| Every Q2+ episode replays (committed evidence path) | **Met for sample Q2** via existing offline-replay CI on source bundles |
| Quality tiers independently auditable | **Met** (schema + manifest tier composition) |
| Negative episodes improve failure diagnosis on held-out tasks | **Partial** — synthetic negatives + benchmark harness present; empirical model uplift deferred |
| Dataset use improves verified tool selection, not mere call frequency | **Deferred (research)** — scoring metric defined; uplift not claimed |
| Releases include datasheets, licenses, benchmark exclusions, known biases | **Met** for v0.1 sample |

## Hard invariant

All Foundry corpus and capture artifacts set `acceptanceInfluence: false` and
MUST NOT be consulted by Lean checkers or theorem acceptance paths.
