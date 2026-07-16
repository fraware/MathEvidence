# Algorithm Assurance contracts (Product 06 MVP)

Machine-readable mirrors of Lean contracts under `MathEvidence.Assurance`.

| Contract | Capability | Level |
| --- | --- | --- |
| `assurance.rational_equality.reference` | `algebra.rational_equality` | verified_reference_algorithm |
| `assurance.linear_algebra.reference` | `algebra.linear_algebra` | verified_reference_algorithm |
| `assurance.finite_counterexample.reference` | `logic.finite_counterexample` | verified_reference_algorithm |

Validate:

```text
python scripts/validate_assurance.py
lake build MathEvidenceAssurance
```

Non-goals: auditing Mathematica/SymPy internals; federated checker soundness.
