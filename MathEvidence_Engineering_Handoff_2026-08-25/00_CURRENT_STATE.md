# 00 — Authoritative Current-State Snapshot


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


## 1. Executive state

MathEvidence already contains substantial infrastructure for evidence-carrying mathematical claims: capability adapters,
evidence schemas/checkers, Lean assurance modules, replay machinery, Certification Record plumbing, benchmarks, adversarial
tests, supply-chain checks, and bounded-execution/security controls.

The remaining problem is not "build the verifier from scratch." It is to make the **promotion boundary** exact and uniformly
enforced across every capability.

PR #53 is an important trust repair. Its core semantic correction is that fixture-backed or nearby theorem replay is not
sufficient evidence that an arbitrary submitted candidate has been theorem-checked. The replayed theorem/check must be
generated from and bound to the candidate actually being certified.

## 2. Pinned CI state

At `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`:

| Gate / workflow | Pinned status | Interpretation |
|---|---|---|
| Security | PASS | Preserve; do not regress while adding generated replay. |
| Adapter conformance | PASS | Existing adapter/schema boundaries are broadly intact. |
| Supply chain | PASS | Current dependency-integrity gate passes. |
| Adversarial | PASS | Existing adversarial baseline passes. |
| Lean | FAIL | Failure occurs after schema/import/audit stages, at the Lean build stage. |
| Offline replay | FAIL | Python replay leg passes; Lean replay leg fails. |
| Benchmarks | FAIL | Benchmark suite passes; separate exact/release-grade job fails while building replay dependencies. |

### What is known

The failure pattern is consistent with a shared Lean/toolchain/vendor/generated-replay integration issue.

### What is not yet established

The retained job metadata does not justify inventing a specific compiler diagnostic. The first engineer must reproduce the
failure on the pinned head and capture the exact `lake build` error, dependency resolution, toolchain version, and generated
module that triggers it.

## 3. Assurance maturity by capability

The table below is the conservative handoff baseline. "Lean contract exists" means the repository contains a Lean-side
reference checker/soundness contract. It does not automatically mean arbitrary candidate bundles may be promoted.

| Capability | Existing assurance asset | Exact candidate-bound generic replay | Theorem-level promotion state |
|---|---|---:|---|
| `algebra.ideal_membership` | Lean/replay path plus exact generator reference implementation | YES, subject to current red Lean build | Intended exact path; keep release promotion blocked until CI/replay is green |
| `algebra.rational_equality` | Lean reference checker/soundness contract | NO generic generator yet | MUST fail closed for exact theorem certification |
| `algebra.linear_algebra` | Lean reference checker/soundness contract | NO generic generator yet | MUST fail closed for exact theorem certification |
| `logic.finite_counterexample` | Lean reference checker/soundness contract | NO generic candidate/witness generator yet | MUST fail closed for certified refutation until exact binding exists |
| `algebra.formal_rational_calculus` | Lean reference checker/soundness contract | Not yet a generic production exact path | MUST remain narrowly scoped and fail closed |
| `analysis.analytic_calculus` | Replay/profile infrastructure exists | NO generic exact theorem generator | MUST fail closed for theorem certification |
| Numerical / heuristic / symbolic evidence paths | Useful evidence/checking machinery | Capability-dependent | Evidence remains valid at its declared class; no theorem upgrade without exact assurance |

## 4. Documentation consistency problem

Historical repository documents contain prior "MET" or equivalent completion claims. Those statements can remain useful as
historical implementation records, but several predate the exact-candidate-binding correction.

Engineers MUST therefore treat status as multidimensional:

- `adapter_exists`
- `checker_exists`
- `lean_soundness_exists`
- `bridge_replay_exists`
- `exact_candidate_binding_exists`
- `offline_replay_exists`
- `certification_record_eligible`

A capability can be complete on several dimensions and still be ineligible for theorem-level promotion.

## 5. Existing architectural strengths to preserve

- Evidence classes are conceptually separated.
- Certification Records are a distinct promotion artifact.
- Lean assurance modules encode useful reference-checker contracts.
- Replay machinery already distinguishes multiple assurance/replay modes.
- Security/adversarial/supply-chain CI exists and is currently green.
- Exact ideal-membership replay provides a practical reference for candidate-bound generation.
- The API now has a fail-closed concept (`assurance_mode_unavailable`) that should become registry-driven.

## 6. Current blockers

### P0 blocker — Lean/exact replay build integration

Until the exact replay path compiles/replays on a clean environment, no expansion of CR eligibility should merge.

### P0 trust-model blocker — status/policy is distributed and partially stale

Assurance eligibility must be represented once, machine-readably, and validated against code/tests/docs.

### P1 implementation gap — generic candidate-bound replay framework

One-off generators will become difficult to audit. The project needs a typed, deterministic generator framework with the
ideal-membership generator migrated as the reference implementation.

### P1 capability gaps

Rational equality, linear algebra, finite counterexample/refutation, and calculus need exact candidate-bound implementations
before any theorem-level promotion.

### P1 provenance/replay gap

Certification Records and replay bundles must bind enough identity to detect candidate, generator, artifact, theorem,
toolchain, and dependency substitution.

## 7. Invariants that must never be weakened

1. Exact assurance requests never silently downgrade to fixture/bridge replay.
2. A benchmark result never grants theorem-level assurance.
3. Numerical agreement never becomes proof by relabeling.
4. A theorem about a fixture or nearby proposition cannot certify a different submitted proposition.
5. Generated Lean must be derived from a validated typed representation, not untrusted raw source fragments.
6. Legacy records must not be silently reinterpreted under stronger semantics.
7. Unsupported capability/mode combinations fail closed.
8. Security limits apply equally to generated replay processes.
