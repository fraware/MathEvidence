# PROJECT_SPEC §19 metrics

Instrumented measurements for verified computational coverage, open replay rate,
and semantic defect rate placeholders. Where in-repo data exists, scripts report
**measured** values; research exits (frontier acceleration, funding, trained
selector uplift) remain OPEN and are never invented.

## Run

```text
# All §19 instrumented metrics (JSON summary to stdout)
python scripts/metrics/run_section19_metrics.py

# Individual
python scripts/metrics/verified_coverage.py
python scripts/metrics/open_replay_rate.py
python scripts/metrics/semantic_defect_rate.py

# Foundry tooling metrics (tool-selection baseline vs reference, corpus quality)
python scripts/metrics/foundry_tool_selection.py
python scripts/metrics/foundry_corpus_quality.py
python scripts/metrics/track_contributions.py

# Or via just
just metrics
just foundry-metrics
```

## Honesty

| Metric | What is measured | What is NOT claimed |
| --- | --- | --- |
| Verified coverage | Share of real-world / bottleneck rows with evidence or capability binding | Fraction of all Lean developments in the wild |
| Open replay rate | Offline replay pass rate over committed bundles | Live backend regeneration success |
| Semantic defect rate | Adversarial + expected-reject fixtures that correctly reject | Expert-audited field defect incidence |
| Tool-selection | Reference vs naive baseline accuracy on `benchmarks/tool_selection` | Trained model held-out uplift |
| Contributions | Count of YAML/JSON records under `docs/foundry/contributions/` | Funding secured or frontier acceleration |
