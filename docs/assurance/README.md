# Algorithm Assurance docs (Product 06)

Independent algorithm-contract documents for owned checkers. These are **not**
thin re-exports of adapter READMEs: each file states input domain, output
relation, reference algorithm steps, soundness, and explicitly null completeness.

Checker / algorithm-contract green is **not** Certification Record eligibility.
Theorem CR requires exact candidate binding and registry `crEligible` — see
[`../STATUS.md`](../STATUS.md) and [`../HANDOFF.md`](../HANDOFF.md).

| Contract doc | Capability | Lean module |
| --- | --- | --- |
| [rational-equality.md](rational-equality.md) | `algebra.rational_equality` | `MathEvidence.Assurance.RationalEquality` |
| [linear-algebra.md](linear-algebra.md) | `algebra.linear_algebra` | `MathEvidence.Assurance.LinearAlgebra` |
| [finite-counterexample.md](finite-counterexample.md) | `logic.finite_counterexample` | `MathEvidence.Assurance.Counterexample` |
| [symbolic-calculus.md](symbolic-calculus.md) | `algebra.formal_rational_calculus` | `MathEvidence.Assurance.Calculus` |

`analysis.analytic_calculus` is a separate owned capability (analytic whitelist;
exact ODE currently empty-obligation single-IC only). Its checker/soundness
surface lives under `MathEvidence.Checkers.AnalyticCalculus` / related modules;
algorithm-contract prose for that ID may be extended here without conflating it
with formal rational calculus.

Machine-readable mirrors: `registry/assurance/`. Validate with
`just assurance-validate`.

**Non-inflation rule:** never upgrade assurance language based on conformance
suite size alone; never claim proprietary CAS verification without source-level
proof obligations; never treat OfflineFixtures as CR authority for a submitted
candidate.
