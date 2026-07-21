# Formal rational calculus checker

Formerly documented as the symbolic calculus checker. The implementation path
remains `MathEvidence.Checkers.Calculus` during PR-Calculus-Reclassification to
avoid a partial filesystem rename; the public capability should be read as
**formal rational calculus**.

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
- Additive alias barrel: `MathEvidence.IR.FormalRationalCalculus` re-exports the
  existing `MathEvidence.IR.CalculusExpr` implementation during the rename path.

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

## Rename path

The safe migration path is:

1. Treat registry text and user-facing docs as `algebra.formal_rational_calculus`.
2. Import `MathEvidence.IR.FormalRationalCalculus` for new Lean references.
3. Keep `MathEvidence.IR.CalculusExpr` and `MathEvidence.Checkers.Calculus`
   available until all downstream adapters, schemas, fixtures, and request
   digests can be migrated in one coordinated change.

Do not claim analytic semantics during or after the rename.
