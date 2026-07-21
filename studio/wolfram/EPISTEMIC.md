# MathEvidence Studio — epistemic contract (Wolfram)

Companion note for `MathEvidenceStudio.wl`.

## Certified gate

```text
AllowCertified ⇔ leanStatus ∈ {
  witness_verified,
  soundness_verified,
  completeness_verified,
  optimality_verified,
  approximation_certified,
  native_verified
}
∧ leanProposition ≠ ""
```

Manifest-only verified statuses without Lean are **Ambiguous**.
Lean status without an exact Lean proposition string is also **Ambiguous**
(Product 09: proposition available before certification).

## Certification surface order

`CertificationSurface` / `CertifyInLean` / `InspectBundle` always render:

1. Proposed Lean proposition (`ShowLeanProposition`)
2. Assumptions / side conditions (`ShowAssumptions`)
3. Epistemic badge (`StudioStateBadge`) — Certified affordance only here

## Calculus vertical

Studio proposes `algebra.formal_rational_calculus` requests. Branch/singularity
conditions live in `domainConditions` and are always shown near the result.
Candidate acceptance never implies completeness of antiderivatives, uniqueness
of ODE solutions, or uniqueness of recurrence closed forms.

Studio invents no checker semantics — Lean/IR/Agent fields only.
