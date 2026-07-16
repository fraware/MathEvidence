# Architecture notes

- Import boundaries (this file)
- `ecosystem-boundaries.md` — what MathEvidence does not replace
- `collaboration-cslib-lean-auto-smt.md` — Milestone 4 federation collaboration
- `federation-agreements.md` — live emit/consume agreements ledger (empty until real)
- `discovery.md` — tactic/CLI discovery orchestration (CI-safe offline default)
- Foundry / frontier notes live under `docs/foundry/` (Milestone 6)
- `canonical-json.md` — digest / canonical JSON profile
- `leanlink-adapter-review.md` — Mathematica transport review + execution notes
- `process-isolation.md` — CPU/memory/wall limits and cancel→kill contract

## Dependency and Import Boundaries

Normative layout and forbidden edges: `docs/REPOSITORY_ARCHITECTURE.md` §11.

## Allowed direction (Lean)

```text
Core → IR → Checkers → Tactic / Registry / Hypothesis / Conjecture / Assurance
TraceToPlan → Core only (plan stubs; agent-side Python owns DAG construction)
Testing is for test targets; production libs must not depend on heavy Testing utils.
```

## Forbidden

- Core / IR / Checkers importing adapters, Tactic orchestration that pulls backends,
  or process/network APIs for theorem acceptance.
- Checkers invoking external processes.
- Foundry participating in acceptance decisions.

## Enforcement

- `scripts/check_import_boundaries.py` (local `just import-boundary`, CI `lean.yml`
  and `security.yml`).
- CODEOWNERS review on Core, Checkers, and trust-model docs.
