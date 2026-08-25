# Exact-certification baseline delta (2026-08-25)

Dated record of how the exact-candidate-binding workstream relates to the
assessed baseline pin. **Live status** lives in [`../STATUS.md`](../STATUS.md)
and [`../HANDOFF.md`](../HANDOFF.md). This file does not rewrite historical audit
evidence.

| Item | Value |
| --- | --- |
| Baseline pin | `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b` ([PR #53](https://github.com/fraware/MathEvidence/pull/53)) |
| Working branch | `phase4/exact-certification-handoff` |
| Current `main` | May still use fixture substitution — not this baseline |
| Engineering archive | [`MathEvidence_Engineering_Handoff_2026-08-25/`](../../MathEvidence_Engineering_Handoff_2026-08-25/) |

## What the pin already contained

Do not rebuild: exact ideal-membership Lean inlining,
`mathevidence-declaration-identity`, generic `assurance_mode_unavailable` for
non-enabled capabilities, stricter `verify_certification_record`, and
substitution forensic tests.

## What this workstream added on the pin

- Maturity inventory + STATUS/HANDOFF rebaseline (registry-backed `cr_eligible`)
- Lean compile fixes required for exact-replay CI (ExprSerialize reserved-word
  binders; related Checker/Encoding/Analytic test modules)
- Typed exact-replay generators for owned capabilities
- Certification Record **v0.4** fields and polarity rules
- Offline release bundles + tamper coverage
- Bounded `lake env lean` execution and argv-only declaration-identity invocation
- CR eligibility enabled only where Lean exact-replay ladders are green

## CR eligibility (after Lean E2E)

| Capability | `cr_eligible` | Notes |
| --- | --- | --- |
| `algebra.ideal_membership_witness` | true | `proved` |
| `algebra.rational_equality` | true | `proved` |
| `algebra.linear_algebra` | true | four ops; `proved` |
| `logic.finite_counterexample` | true | `refuted` |
| `algebra.formal_rational_calculus` | true | four ops with `soundResult` |
| `analysis.analytic_calculus` | true | Deriv / DerivWithin / Antideriv / ODE (empty-obligation single-IC) |
| Federated SAT / PB / SMT | false | metadata only |

Offline exact driver defaults to `theorem_pending`. With
`MATHEVIDENCE_OFFLINE_LEAN=1` / `require_lean=True` and Lake available it can
reach `theorem_proved` after declaration-identity inspect (still not a CR mint).
Online `kernel_replay` remains the primary promotion path.

## Pin-era CI note (historical)

At the pin assessment (2026-08-25), security / adapter-conformance / supply-chain
/ adversarial were green while `lean`, `offline-replay`, and
`ideal-release-grade` failed on a shared Lean parse error in
`MathEvidence.Core.ExprSerialize` (reserved word `prefix` used as a pattern
binder). That class of failure, plus independent Checker test-module fixes, was
addressed on this workstream. Treat the long diagnostic log under the archive
and older commits as historical reproduction — not current live status.

## Forbidden non-fixes (still)

Do not skip generated modules, weaken theorems, disable sorry/axiom/import
audits, or convert exact replay back to fixture replay to “green” CI.
