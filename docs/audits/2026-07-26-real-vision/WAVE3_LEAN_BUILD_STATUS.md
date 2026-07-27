# Wave 3 Lean build status (ME-RV-030..036)

Date: 2026-07-26

## Intent

Wave 3 delivers the ideal-membership flagship:

- Fixed-arity sparse polynomial IR (`Vector Nat m` / erased wire with arity reject)
- Interpretation + normalization soundness into `MvPolynomial (Fin m) ℤ`
- Typed request/certificate + `checkBool` / `checkMembership_sound`
- Proof-producing reifier + `mathevidence_ideal` (backends: sympy|sage|mathematica|replay|lean_reference_search)
- Benchmark scores **proposed** multipliers (oracle `expectedMultipliers` only)
- Capability rename `algebra.groebner_membership` → `algebra.ideal_membership_witness`

## Local Lake / Mathlib

**Resolution fixed** (see [`MATHLIB_RESOLUTION.md`](MATHLIB_RESOLUTION.md)).
`MathEvidenceCore` and `mathevidence-verify-bundle` build locally. Full
`MathEvidenceCheckers` / Mathlib-heavy targets may still require a long first
Mathlib compile and are not claimed green here.

Correct Lean sources are committed under:

- `MathEvidence/IR/Polynomial/{Syntax,Normalize,Interpret,Soundness}.lean`
- `MathEvidence/Checkers/IdealMembership/{Spec,Certificate,Check,Soundness,Wire,Search}.lean`
- `MathEvidence/Tactic/{ReifyPolynomial,IdealMembership}.lean`

When Mathlib resolves:

```text
lake build MathEvidenceCheckers
lake env lean MathEvidence/Checkers/IdealMembership/Check.lean
```

## Verification without Lean

```text
python -m pytest adapters/common/test_ideal_membership.py agent/test_agent_api.py -q
python scripts/run_ideal_membership_benchmark.py
```

Benchmark honesty: never emits `soundness_verified` without a Certification Record;
Lean/kernel fields report `smoke_unavailable` / `stub_pending_mathlib` when Lake is blocked.

## GitHub issues

- https://github.com/fraware/MathEvidence/issues/18 — ME-RV-030
- https://github.com/fraware/MathEvidence/issues/19 — ME-RV-031
- https://github.com/fraware/MathEvidence/issues/20 — ME-RV-032
- https://github.com/fraware/MathEvidence/issues/21 — ME-RV-033
- https://github.com/fraware/MathEvidence/issues/22 — ME-RV-034
- https://github.com/fraware/MathEvidence/issues/23 — ME-RV-035
- https://github.com/fraware/MathEvidence/issues/24 — ME-RV-036
