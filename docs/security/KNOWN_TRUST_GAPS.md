# Known limitations and trust gaps

This document lists **current, honest limitations** of the MathEvidence public
preview. It is part of the trust surface. Experimental capabilities must not be
presented as stable, and human/external gates must not be invented.

All registry capabilities remain `"status": "experimental"` until the
[stable promotion checklist](../validation/stable-capability-checklist.md) and
[GOVERNANCE.md](../../GOVERNANCE.md) requirements are met with real artifacts.

For machine-readable CR maturity, use
[`registry/maturity-inventory.json`](../../registry/maturity-inventory.json).
For the short public status, use [`docs/STATUS.md`](../STATUS.md). Historical
dated audits are evidence of their date, not current promotion authority.

---

## Trust invariants

These do not change with backend, benchmark, or release status.

- External backends, models, search procedures, and adapters are untrusted.
- Lean/checker authority is capability-specific and must match the advertised
  proposition.
- A backend Boolean answer is never sufficient theorem evidence.
- A fixture or nearby theorem cannot certify a different submitted candidate.
- Theorem-level Certification Records require exact candidate binding and live
  registry CR eligibility.
- Assurance may not be escalated by an adapter, serializer, receipt field, user
  flag, benchmark result, or fallback path.
- Unsupported exact modes fail closed.
- Counterexample certification has polarity `refuted`, not `proved`.
- Numerical agreement is not exact proof by relabeling.
- Failure to find a counterexample is not a proof of universality.
- Historical records retain the semantics under which they were created; they
  are not silently upgraded when a later version gains stronger assurance.

Forensic regressions under `tests/forensic/` guard these properties.

---

## Current engineering posture

Exact candidate binding is the theorem-CR rule
([ADR 0005](../adr/0005-exact-candidate-binding.md)). CR eligibility is
registry-backed, and the required `lean` workflow executes production-generated
candidate modules for every CR-eligible capability. Structural source
generation alone is not sufficient release evidence.

| Area | Honest status |
| --- | --- |
| Exact binding / CR | Five owned capabilities are registry-eligible for exact CR (`proved`, except finite CEX `refuted`). Rational equality is deliberately non-eligible for theorem CR in the pinned Lean 4.14 public preview. Federated SAT/PB/SMT remain non-eligible. |
| Ideal membership | Witness identity only (`algebra.ideal_membership_witness`); no Gröbner-basis, non-membership, radical, minimality, or completeness claim. |
| Rational equality | Checker, soundness theorem, bridge, and exact-source generation remain. Candidate-specific theorem CR is disabled fail-closed because the pinned Lean 4.14 production native-reduction path does not admit the generated checker proposition without an unacceptable `sorryAx` dependency. Binary floating point is not silently promoted to exact arithmetic. |
| Linear algebra | Exact rational `inverse_witness`, `system_solution`, `kernel_vector`, and `det_identity`; no broad linear-algebra completeness/rank/basis claim. |
| Finite counterexample | Exact finite witness can establish `refuted`. No-witness or sampled search cannot establish the universal claim. |
| Formal calculus | `algebra.formal_rational_calculus` is a formal/algebraic grammar, not general analytic calculus. |
| Analytic calculus | `analysis.analytic_calculus` is a strict theorem-form whitelist, not arbitrary analysis. Exact ODE support retains its documented obligation/initial-condition restrictions. |
| Evidence bundles | Candidate Bundle v0.3; Certification Record v0.4 for exact promotion. Legacy records must not be silently upgraded. |
| Offline bundle replay | Available where declared: sealed candidate artifacts can be regenerated/validated without consulting the solver after materialization. This may end at `theorem_pending`. |
| Offline kernel replay | Tracked separately as `offline_kernel_replay_exists`. It is currently **false** as a release maturity property; optional Lean execution succeeding on a machine is not the same as a required, network-isolated release gate. |
| Bundle verifier | `mathevidence-verify-bundle` emits operational checker status only. It is not theorem Certification authority. |
| CI / local checks | Local `just check` is useful feedback, not release attestation. Exact release claims require green remote gates on the exact release SHA. |
| Repository rules | Branch protection/rulesets are operational governance choices for this experimental preview. They are not mathematical assurance evidence and are not a public-preview release prerequisite. |
| Stable promotion | **Blocked** until the repository-defined human/domain/trust/external gates close. Experimental CR eligibility and stable lifecycle promotion are separate. |
| CODEOWNERS | Single-owner incubation stub (`@fraware`). Multi-area dual review is not enforceable yet. |
| Signing / PKI | Production receipt PKI and production release signing remain deferred. Dev keys are not production authority. The experimental release workflow records unsigned status explicitly rather than claiming a signature. |

---

## Open human and governance gates — blocking `stable`

| ID | Limitation | Where to record progress |
| --- | --- | --- |
| H-1 | ≥3 external Milestone 0 user confirmations | `docs/validation/user-confirmation.md` (0 completed) |
| H-2 | ≥1 external workflow-win confirmation (§21.10) | `docs/validation/workflow-win-log.md` |
| H-3 | Independent domain + trust-model reviews for stable promotion | `docs/validation/review-packets/`, `stable-capability-checklist.md` |
| H-4 | Live federation agreements with ≥2 external peers | `docs/validation/federation-live-checklist.md`, `docs/architecture/federation-agreements.md` |
| H-5 | Studio usability results with ≥3 completed sessions | `docs/validation/studio/usability/` |
| H-6 | Expert judgments for hypothesis interfaces / conjecture precision / TTP graph | `docs/validation/review-packets/` |
| H-7 | Real multi-area CODEOWNERS / dual approval | `.github/CODEOWNERS`, `GOVERNANCE.md` |

The `semanticReview` and `trustReview` registry fields refer to this
**stable-promotion human review layer**. Their `absent` state is intentional and
must not be presented as completed review. They are distinct from the mechanical
exact-candidate CR gate used by this experimental preview.

Wave-8 human scaffolding remains blocked until real external artifacts exist;
templates are not confirmations.

---

## Open engineering and product gaps

| ID | Limitation | Notes |
| --- | --- | --- |
| E-1 | Immutable all-green release commit | The final tagged SHA must have the required assurance/security/replay/conformance gates green. |
| E-2 | Repository governance hardening | Optional operational hardening for this experimental preview; not a mathematical-assurance or release prerequisite. |
| E-3 | Lean toolchain changes | `lean-toolchain` is pinned; a bump requires a separately validated change. |
| E-4 | LeanLink native Mathematica bridge | Deferred; live Mathematica transport is `wolframscript` when configured. |
| E-5 | Sage rational equality | Declared/placeholder; not advertised as live Agent routing. |
| E-6 | Analytic-calculus completeness | Out of scope. Only the registered whitelist and explicit hypotheses are supported. |
| E-7 | Production receipt PKI / release signing identity | Deferred; no dev key or soft signing attempt may be marketed as production signing. |
| E-8 | Foundry frontier / funding exits | Tiny-suite tool-selection results do not establish frontier acceleration or maintenance funding. |
| E-9 | Independent external reproduction | Release artifacts are designed for it; third-party reproduction remains external work and must not be fabricated. |
| E-10 | Ideal flagship adoption | Exact candidate path exists, but live external adoption/held-out validation remains open. |
| E-11 | Windows native Lake link | Required workaround remains `scripts/link_exe_via_rsp.py`; degrade with dependency/setup status, never fake Certified. |
| E-12 | Practical LA scale | Exact determinant/checker cost and the IR size policy intentionally bound practical dimensions; this is not a completeness claim. |
| E-13 | Lean internal expression identity | Compiler-internal `Expr.hash` stability across revisions is not claimed as a protocol guarantee. |
| E-14 | Rational theorem CR on pinned Lean 4.14 | Disabled fail-closed for this public preview. Re-enabling requires a candidate-specific production theorem path that passes without `sorryAx` and is then requalified on an exact release SHA. |

Environment-level Lean import/axiom audits are **implemented** through the
`mathevidence-import-graph` / `mathevidence-axiom-report` drivers and CI; source
scans remain defense in depth.

---

## Capability naming and claim-scope notes

- Public formal-calculus ID: `algebra.formal_rational_calculus`.
- Public analytic-calculus ID: `analysis.analytic_calculus`; strict whitelist
  only.
- Ideal-membership ID: `algebra.ideal_membership_witness`; witness identity
  only.
- Rational equality must not be described as theorem-CR eligible in this pinned
  Lean 4.14 release, even though its checker/soundness/bridge code exists.
- Linear algebra must be described operation-by-operation, not as generic
  verified linear algebra.
- Legacy fixture/conformance directories may use historical names such as
  `calculus` or `symbolic_calculus`; directory names do not broaden the public
  mathematical claim.
- Do not advertise a live registry capability that does not exist.

---

## Benchmark interpretation

The frozen ideal-membership release corpus is a **release conformance and
assurance-regression corpus**. It is useful for deterministic implementation
checks, mutation testing, answer/evidence separation, and observed false-accept
behavior on that corpus.

It does **not** by itself establish a population false-accept probability,
universal solver soundness, broad mathematical generalization, or formal
checker soundness. Formal assurance comes from the declared checker/soundness
argument within its exact scope; empirical suites test the implementation and
integration of that argument.

The critical failure cell remains:

> answer incorrect + evidence verified

Any such deterministic release-corpus event is a release blocker.

---

## Release truth rule

For a release claim, prefer evidence in this order:

1. the mathematical proposition actually established;
2. executable checker/verifier implementation;
3. adversarial and contract tests;
4. exact-SHA CI / replay evidence;
5. machine-readable capability and maturity registry;
6. current status documentation;
7. historical audits and roadmap labels.

Documentation cannot strengthen a weaker checker.
