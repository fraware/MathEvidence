# Registry data

Machine-readable capability and backend declarations (Product 07).
No capability may be marked `stable` from documentation alone.

## Layout

- `catalog.json` — discovery index of capability and backend files
- `capabilities/` — validated against `schemas/capability.schema.json`
- `backends/` — validated against `schemas/backend.schema.json`

## Support layers

Queries distinguish:

1. **declared** — present in registry
2. **installed** — local adapter/runtime discovery (Agent API / adapter `initialize`)
3. **conformance-verified** — `supportClaims.conformanceVerified` / backend `supportLevel`

## Capabilities

| ID | Ownership | Status | Notes |
| --- | --- | --- | --- |
| `algebra.rational_equality` | owned | experimental | Milestone 1 reference path — see `docs/validation/stable-capability-checklist.md` before `stable` |
| `algebra.linear_algebra` | owned | experimental | Exact matrix witnesses |
| `logic.finite_counterexample` | owned | experimental | Finite typed witnesses |
| `algebra.groebner_membership` | federated | experimental | Metadata only; external checker |
| `logic.sat_unsat` | federated | experimental | Metadata only; external checker |
| `logic.pseudo_boolean` | federated | experimental | Metadata only; external checker |
| `logic.smt` | federated | experimental | Metadata only; Lean-SMT authority |

Federated entries use `ownership: "federated"` and
`schemas/federation-metadata.schema.json`. See
`docs/architecture/collaboration-cslib-lean-auto-smt.md` and
`evidence/federation/examples/`.

Assurance contracts for owned checkers: `registry/assurance/`.

Foundry corpus releases are **not** capability registry entries. See
`foundry/releases/catalog.json` and `docs/foundry/`.

## Validate

```text
python scripts/validate_registry.py
python scripts/validate_federation.py
python scripts/validate_assurance.py
```

CI runs the same gates via `just registry-validate` / `federation-validate` /
`assurance-validate`.
