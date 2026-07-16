# Algorithm Assurance docs (Product 06)

Independent algorithm-contract documents for owned checkers. These are **not**
thin re-exports of adapter READMEs: each file states input domain, output
relation, reference algorithm steps, soundness, and explicitly null completeness.

| Contract doc | Capability | Lean module |
| --- | --- | --- |
| [rational-equality.md](rational-equality.md) | `algebra.rational_equality` | `MathEvidence.Assurance.RationalEquality` |
| [linear-algebra.md](linear-algebra.md) | `algebra.linear_algebra` | `MathEvidence.Assurance.LinearAlgebra` |
| [finite-counterexample.md](finite-counterexample.md) | `logic.finite_counterexample` | `MathEvidence.Assurance.Counterexample` |
| [symbolic-calculus.md](symbolic-calculus.md) | `analysis.symbolic_calculus` | `MathEvidence.Assurance.Calculus` |

Machine-readable mirrors: `registry/assurance/`. Validate with
`just assurance-validate`.

**Non-inflation rule:** never upgrade assurance language based on conformance
suite size alone; never claim proprietary CAS verification without source-level
proof obligations.
