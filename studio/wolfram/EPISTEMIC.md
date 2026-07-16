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
```

Manifest-only verified statuses without Lean are **Ambiguous**.

## Calculus vertical

Studio proposes `analysis.symbolic_calculus` requests. Branch/singularity
conditions live in `domainConditions` and are always shown near the result.
Candidate acceptance never implies completeness of antiderivatives, uniqueness
of ODE solutions, or uniqueness of recurrence closed forms.
