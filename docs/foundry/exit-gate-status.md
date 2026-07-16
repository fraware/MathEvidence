# Milestone 6 exit-gate status

Tracked against `docs/DELIVERY_ROADMAP.md` Milestone 6 and Product 08 acceptance
criteria. Engineering artifacts can be met in-repo; research / funding / live
collaboration criteria cannot be closed by code alone.

**Honesty:** Do not claim live frontier acceleration or funding secured.
Tool-selection numbers below distinguish (a) reference vs naive harness check,
(b) a **trivial trained** bag-of-token selector vs naive — not a frontier model.

## Deliverables

| Deliverable | Status | Artifact |
| --- | --- | --- |
| Public certified tool-use corpus | **Met (sample)** | `foundry/corpus/v0.1/` (12 episodes) |
| Provenance, quality tiers, contamination controls | **Met** | corpus schemas + `contamination.json` / `splits.json` / datasheet |
| Verification-aware tool-selection benchmark | **Met (harness)** | `benchmarks/tool_selection/` + `scripts/run_tool_selection_benchmark.py` |
| Baseline vs reference metrics | **Met (engineering)** | `scripts/metrics/foundry_tool_selection.py` — harness self-check |
| Trivial trained selector vs naive | **Met (measured)** | `scripts/metrics/foundry_trained_selector.py` / `just foundry-train-eval` — see numbers below |
| Corpus build-quality metrics | **Met (engineering)** | `scripts/metrics/foundry_corpus_quality.py` |
| Frontier collaborations scaffolding | **Met (notes)** | `docs/foundry/frontier-collaborations.md` |
| Measured library contribution tracking | **Met (script + empty ledger)** | `scripts/metrics/track_contributions.py`; `docs/foundry/contributions/` (0 records) |
| Maintenance funding / ownership plan | **Met (plan doc)** | `docs/foundry/maintenance-ownership.md` — funding **not secured** |
| Pipelines from evidence/episodes without acceptance influence | **Met** | `foundry/pipelines/` |
| §19 instrumentation | **Met (engineering)** | `scripts/metrics/` (`verified_coverage`, `open_replay_rate`, `semantic_defect_rate`) |

## Trained selector measurement (2026-07-16)

| Field | Value |
| --- | --- |
| Method | Rule + learned bag-of-token weights (seeded synonym lexicon + additive counts from corpus train); pure Python; no sklearn required |
| Train | `foundry/corpus/v0.1` split `train` (**8** episodes) |
| Eval | `benchmarks/tool_selection` (**8** tasks; held-out relative to corpus train) |
| Naive accuracy | **37.5%** (3/8) — always `algebra.rational_equality` + `soundResult` |
| Trained accuracy | **100%** (8/8) on this small public suite |
| Lift (trained − naive) | **+62.5 pp** |
| Command | `just foundry-train-eval` |
| acceptanceInfluence | **false** (never feeds Lean acceptance) |

**Caveats (honest):** the eval suite is tiny (n=8); synonym seeds and a few
safety rules (shell / unknown-cap refusal; candidate≠completeness) contribute.
This does **not** claim frontier-grade selection, library acceleration, or that
Milestone 6 research exits for funding/frontier are closed. Re-run after corpus
growth; lift may shrink.

## Exit criteria

| Criterion | Status | Notes |
| --- | --- | --- |
| Data improves held-out verified tool use | **PARTIAL (research)** | Trivial trained selector shows measured lift vs naive on `tool_selection` (`just foundry-train-eval`). Reference harness check remains separate (`just foundry-metrics`). Frontier-grade uplift still not claimed. |
| ≥1 frontier program materially accelerated | **OPEN (human / external)** | Collaboration notes only; no live acceleration claimed |
| Maintenance funding and ownership established | **OPEN / partial** | Ownership map documented; funding **not secured** |

## Product 08 acceptance criteria

| Criterion | Status |
| --- | --- |
| Every Q2+ episode replays (committed evidence path) | **Met for sample Q2** via existing offline-replay CI on source bundles |
| Quality tiers independently auditable | **Met** (schema + manifest tier composition + `foundry_corpus_quality`) |
| Negative episodes improve failure diagnosis on held-out tasks | **Partial** — synthetic negatives + benchmark harness present; empirical frontier-model uplift OPEN |
| Dataset use improves verified tool selection, not mere call frequency | **PARTIAL** — trivial trained selector measured vs naive (`foundry_trained_selector.py`); not a production/frontier selector |
| Releases include datasheets, licenses, benchmark exclusions, known biases | **Met** for v0.1 sample |

## How to measure (engineering)

```text
just foundry-metrics
just foundry-train-eval
just metrics
```

## Hard invariant

All Foundry corpus and capture artifacts set `acceptanceInfluence: false` and
MUST NOT be consulted by Lean checkers or theorem acceptance paths.
