# Registry data

Machine-readable capability and backend declarations (Product 07).
No capability may be marked `stable` from documentation alone.

## Layout

- `catalog.json` — discovery index of capability and backend files
- `capabilities/` — validated against `schemas/capability.schema.json`
- `backends/` — validated against `schemas/backend.schema.json`
- `maturity-inventory.json` — independent assurance-maturity booleans and
  Certification Record eligibility (validated against
  `schemas/maturity-inventory.schema.json`; `docs/STATUS.md` must match).
  Operator runbook: [`docs/HANDOFF.md`](../docs/HANDOFF.md).

## Support layers

Queries distinguish:

1. **declared** — present in registry
2. **installed** — local adapter/runtime discovery (Agent API / adapter `initialize`)
3. **conformance-verified** — `supportClaims.conformanceVerified` / backend `supportLevel: conformance_verified`

Backend/capability `supportLevel` values (honesty for fixture vs live):

| Level | Meaning |
| --- | --- |
| `declared` | Named in registry; no claim of working generator or fixtures |
| `placeholder` | Adapter stub / fixture mode only; no dual-backend evidence |
| `implemented` | Live path exists for some fragment (prefer finer levels when distinguishing fixtures) |
| `offline_fixtures_passing` | Committed evidence from this backend replays offline; live may be incomplete |
| `live_generator_complete` | Full declared-fragment live generator |
| `conformance_verified` | Required conformance cases pass for this backend path |

Do **not** use `implemented` or `live_generator_complete` for scaffold-only live paths.
`algebra.rational_equality` has dual-backend evidence: SymPy
`conformance_verified` + Mathematica `live_generator_complete` (wolframscript when
`MATHEVIDENCE_WOLFRAMSCRIPT` is set; public CI without Wolfram still uses offline
fixtures / differential `skip`/`fixture`). LeanLink remains scaffold
(`docs/architecture/leanlink-adapter-review.md`).

## Capabilities

| ID | Ownership | Status | Notes |
| --- | --- | --- | --- |
| `algebra.rational_equality` | owned | experimental | Exact-bound; CR-eligible (`proved`) after Lean E2E — see maturity inventory |
| `algebra.linear_algebra` | owned | experimental | Exact-bound; CR-eligible (`proved`) for registered ops |
| `logic.finite_counterexample` | owned | experimental | Exact-bound; CR-eligible (`refuted`) |
| `algebra.formal_rational_calculus` | owned | experimental | Formal rational identities only; CR-eligible (`proved`); not analytic semantics |
| `analysis.analytic_calculus` | owned | experimental | Analytic whitelist; CR-eligible (`proved`); ODE empty-obligation single-IC only |
| `algebra.ideal_membership_witness` | owned | experimental | Exact-bound; CR-eligible (`proved`); witness identity only |
| `logic.sat_unsat` | federated | experimental | Metadata only; never CR-eligible under exact binding |
| `logic.pseudo_boolean` | federated | experimental | Metadata only; never CR-eligible under exact binding |
| `logic.smt` | federated | experimental | Metadata only; Lean-SMT authority |

Federated entries use `ownership: "federated"` and
`schemas/federation-metadata.schema.json`. See
`docs/architecture/collaboration-cslib-lean-auto-smt.md` and
`evidence/federation/examples/`.

`assurancePolicy.certification.crEligible` (mirrored in
`maturity-inventory.json`) is the only authority for theorem-level Certification
Record minting. OfflineFixtures and checker-only green are not CR authority.

Assurance contracts for owned checkers: `registry/assurance/`.

Foundry corpus releases are **not** capability registry entries. See
`foundry/releases/catalog.json` and `docs/foundry/`.

Honest §21 / milestone mapping: `docs/validation/remaining-spec-matrix.md`.

## Validate

```text
python scripts/validate_registry.py
python scripts/validate_maturity_inventory.py
python scripts/validate_federation.py
python scripts/validate_assurance.py
```

CI runs the same gates via `just registry-validate` / `federation-validate` /
`assurance-validate`.
