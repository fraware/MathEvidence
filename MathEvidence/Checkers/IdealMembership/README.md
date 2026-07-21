# Ideal membership checker

Status: native witness checker present; flagship value gate still partial.

## Planned Claim

Given a target polynomial `f` and generators `{g_i}`, a certificate supplies
multiplier polynomials `{q_i}` and establishes only:

```text
f = sum_i q_i * g_i
```

The current Lean checker authoritatively checks the sparse-polynomial identity
after normalization. That checked identity is the certificate boundary for the
membership claim:

```text
f ∈ Ideal.span {g_i}
```

## Current Scope

- Registry capability: `algebra.groebner_membership`.
- Sparse integer-polynomial syntax: `MathEvidence.IR.Polynomial.Syntax`.
- Checker: `checkMembership` in `MathEvidence.Checkers.IdealMembership.Check`.
- Meta auto-bridge: univariate `Ideal.span` (singleton + two gens) and
  `MvPolynomial (Fin 2/3)` with grevlex exact division for non-monomial
  principal generators (when an exact ℤ quotient exists) plus monomial gens;
  Fin 4 Meta close not wired (reify accepts `n≤4`).
- Certificate schema: `schemas/ideal-membership-certificate.schema.json`.
- Open backend: SymPy can live-generate simple multiplier witnesses; Lean/Python
  mirror checking remains authoritative.
- Sage and Mathematica are not advertised as live ideal-membership generators in
  this repository until live conformance evidence exists.
- Benchmark: `benchmarks/ideal_membership` numeric harness ≥50 tasks (55).

## Explicitly Out Of Scope

- Gröbner basis computation.
- Canonical basis, minimality, or uniqueness claims.
- Radical membership or ideal equality.
- Completeness or performance guarantees for external projects.

Do not mark the flagship value gate closed until the benchmark reaches at least
50 real tasks, backend conformance is recorded honestly, and the Mathlib theorem
bridge is documented.
