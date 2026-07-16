# Symbolic calculus checker

## Claim

Establishes a **candidate** formal identity for Milestone 5 operations
(Project Spec Phase 5 / Delivery Roadmap Milestone 5):

| Operation | Established obligation |
| --- | --- |
| `derivative_candidate` | `formalDeriv(f) = g` as rational functions |
| `antiderivative_candidate` | `formalDeriv(F) = f` on the listed domain |
| `recurrence_identity` | `u(n+1) = rhs[u ↦ u(n)]` for closed form `u` |
| `ode_candidate` | `y' = f(x,y)` after substituting solution `y`, plus ICs |

## Assurance

- Mode: `kernel_replay` (Lean formal differentiation / substitution + `polyEqual`).
- Backends are untrusted generators only.

## Explicitly out of scope

- Completeness of antiderivatives
- Uniqueness of ODE solutions
- That a recurrence determines a unique sequence
- Analytic differentiability beyond the rational fragment
- Identity at poles / singularities

Candidate validity **never** implies completeness.

## Domain / singularity conditions

Every division denominator appearing in the claim expressions must appear in
`domainConditions`. Empty conditions are allowed only when there are no
divisions. Conditions are echoed on the certificate and must match the request.

## Algorithm

1. Bind certificate `requestDigest` and `operation` to the request.
2. Reject ill-formed / oversized expressions.
3. Require domain coverage of all denominators.
4. Dispatch on `operation` and accept only when the formal identity holds.

## Offline replay

`Replay.lean` reruns `check` with no adapter invocation.
Hand-written fixtures live in `Tests.lean` and discharge with `native_decide`.

## Axiom / `sorry` audit

- Project `sorry`: none in this checker or `IR/CalculusExpr`.
- Project-specific axioms: none.
