# Benchmarks

- `real_world/` — curated formalization bottlenecks
- `adversarial/` — semantic traps and malformed evidence
- `conformance/` — backend-independent expected behavior
- `agent/held_out/` — held-out Agent API task set (Milestone 2)
- `tool_selection/` — verification-aware tool-selection suite (Milestone 6)

## Agent held-out

```text
python scripts/run_agent_held_out.py
```

## Tool selection

Scores correct capability and claim-class selection under verification
constraints (not mere call frequency). Immutable; excluded from Foundry train.

```text
python scripts/run_tool_selection_benchmark.py
just tool-selection
```
