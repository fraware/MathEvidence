# Benchmarks

- `real_world/` — curated formalization bottlenecks (`just real-world`)
- `adversarial/` — semantic traps and malformed evidence (`just adversarial` / `just adversarial-exec`)
- `metamorphic/` — rename / reassoc / redundant-assumption suite (`just metamorphic`)
- `perf/` — last perf-budget run artifact (`just perf-budgets`)
- `conformance/` — pointer to `evidence/conformance/`
- `agent/held_out/` — held-out Agent API task set (Milestone 2)
- `tool_selection/` — verification-aware tool-selection suite (Milestone 6)
- `differential/` — dual-backend differential harness results

## Agent held-out

```text
python scripts/run_agent_held_out.py
```

## Real-world

```text
python scripts/run_real_world.py
just real-world
```

## Tool selection

Scores correct capability and claim-class selection under verification
constraints (not mere call frequency). Immutable; excluded from Foundry train.

```text
python scripts/run_tool_selection_benchmark.py
just tool-selection
```
