# Ideal membership checker

Status: Wave 3 flagship path — fixed-arity IR, `checkMembership_sound` authority,
capability `algebra.ideal_membership_witness`.

## Claim

Given target `f` and generators `{g_i}`, a certificate supplies multipliers
`{q_i}` establishing:

```text
f = sum_i q_i * g_i
```

Lean `checkBool` / `checkMembership` is the Boolean gate. The authority theorem
`checkMembership_sound` / `checkBool_sound` lifts acceptance to:

```text
f.eval ∈ Ideal.span (Set.range g.eval)
```

in `MvPolynomial (Fin m) ℤ`.

## Modules

- IR: `MathEvidence.IR.Polynomial.{Syntax,Normalize,Interpret,Soundness}`
- Checker: `MathEvidence.Checkers.IdealMembership.{Spec,Certificate,Check,Soundness,Wire}`
- Kernel replay: `ReplaySound` + `OfflineFixtures` (`xy`, `x2m1`)
- Search (untrusted): `MathEvidence.Checkers.IdealMembership.Search` (`lean_reference_search`)
- Tactic: `mathevidence_ideal` / `mathevidence_ideal_membership`
- Schemas: `schemas/ideal-membership-{request,certificate}.schema.json`
- Benchmark: `scripts/run_ideal_membership_benchmark.py`
  - `--tier candidate` (default / smoke / `just check`): propose + Python mirror; never `soundness_verified`
  - `--tier release` (nightly / `benchmarks.yml`): OfflineFixtures + Certification Record

## Held-out honesty

In-repo `held_out` stratum tasks are synthetic. External library-derived held-out
(ME-RV-081) remains **BLOCKED(human)** until licensed sources are supplied.

## Explicitly out of scope

- Gröbner basis correctness / reduction certificates
- Non-membership, radical membership, ideal equality
- Completeness or optimality of search

## Lake note

See `docs/audits/2026-07-26-real-vision/WAVE3_LEAN_BUILD_STATUS.md` when Mathlib
cannot resolve locally.
