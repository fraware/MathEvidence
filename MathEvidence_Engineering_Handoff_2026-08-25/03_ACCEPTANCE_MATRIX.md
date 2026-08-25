# 03 — Program Acceptance Matrix


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


The project reaches the intended engineering vision when every required row below is evidenced by code/tests at the release
commit. This matrix supersedes any older blanket "MET" interpretation for the purposes of this handoff.

| ID | Requirement | Required evidence | Exit condition |
|---|---|---|---|
| A01 | Assurance labels match actual verification | Registry + policy tests | Unsupported modes fail closed |
| A02 | Exact theorem certification is candidate-bound | Generator + mismatch tests | No fixture substitution can pass |
| A03 | Capability status is machine-readable | Versioned registry | Docs/API/tests validate against same source |
| A04 | Lean assurance build is reproducible | Clean CI `lake build` | Green on pinned release head |
| A05 | No sorry/axiom policy regression | Existing audit gates | Green after generated replay changes |
| A06 | Exact replay generation is deterministic | Golden/hash tests | Same inputs/version => same source/hash |
| A07 | Generated source is injection-resistant | Typed IR + adversarial tests | No raw untrusted Lean fragment path |
| A08 | Rational equality exact path is scoped and sound | E2E positive/negative tests | CR enabled only for exact supported grammar |
| A09 | Linear algebra exact path is operation-scoped | Per-operation E2E tests | No generic overclaim |
| A10 | Counterexample semantics distinguish refutation | Record schema + tests | Valid witness produces `refuted`, not `proved` |
| A11 | Calculus exact path is narrowly formalized | Grammar/hypothesis tests | Unsupported analytic claims fail closed |
| A12 | CR binds candidate identity | Canonical hash + tamper tests | Candidate mutation invalidates verification |
| A13 | CR binds generator/verifier/toolchain identity | Record + replay validation | Version/dependency substitution detected |
| A14 | Legacy records cannot silently upgrade | Migration tests | Old fixture-backed records stay lower assurance |
| A15 | Offline replay works | Network-disabled replay test | CR-eligible bundle replays cleanly |
| A16 | Replay bundle integrity is checked | Manifest/hash tests | Missing/corrupt artifacts fail |
| A17 | Benchmark score cannot alter assurance | Policy tests | Benchmark outputs never grant CR eligibility |
| A18 | CI diagnoses setup vs science failure | Job structure | Benchmark prerequisite failures are distinct |
| A19 | Bounded execution covers generated replay | timeout/output/process/path tests | No bypass through Lean generator path |
| A20 | Security/adversarial/supply-chain baselines remain green | CI | No regression |
| A21 | Capability onboarding is documented | Runbook | New engineer can add a capability without inference |
| A22 | Current-state docs are truthful | Generated/validated status | No stale CR-eligibility claims |
| A23 | Every CR-eligible capability has exact mismatch tests | Test inventory | One intentional semantic mutation fails per bound field class |
| A24 | Every certification outcome has explicit polarity/scope | Schema + API tests | `proved`, `refuted`, evidence-only outcomes cannot be conflated |

## Capability release matrix

A capability may set `cr_eligible: true` only if all applicable cells below are green.

| Capability | Checker | Lean contract | Exact binding | Exact E2E | Offline replay | Tamper tests | Policy enable |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ideal membership | existing | existing | existing reference path | must be green | must be green | required | conditional |
| Rational equality | existing | existing | TO BUILD | TO BUILD | TO BUILD | TO BUILD | BLOCKED |
| Linear algebra | existing | existing | TO BUILD | TO BUILD | TO BUILD | TO BUILD | BLOCKED |
| Finite counterexample | existing | existing | TO BUILD | TO BUILD | TO BUILD | TO BUILD | BLOCKED |
| Formal rational calculus | existing | existing | TO BUILD/FORMALIZE | TO BUILD | TO BUILD | TO BUILD | BLOCKED |
| Analytic calculus | partial/profile | capability-specific | TO DESIGN NARROWLY | TO BUILD | TO BUILD | TO BUILD | BLOCKED |

"Existing" in this table refers to the pinned repository assets, not a blanket assertion that the full end-to-end path is
currently green.
