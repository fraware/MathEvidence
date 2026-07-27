# Known limitations and trust gaps

This document lists **honest limitations** of the MathEvidence public preview.
It is part of the trust surface: do not treat experimental capabilities as
stable, and do not invent human confirmations to close the gates below.

All registry capabilities remain `"status": "experimental"` until the
[stable promotion checklist](../validation/stable-capability-checklist.md)
and [governance](../../GOVERNANCE.md) requirements are met with real artifacts.

For a short project status summary, see [`docs/STATUS.md`](../STATUS.md).
For the 2026-07-26 triple-check, see
[`audits/2026-07-26-real-vision/TRIPLE_CHECK_GAP_MATRIX.md`](../audits/2026-07-26-real-vision/TRIPLE_CHECK_GAP_MATRIX.md).

---

## Trust invariants (always)

- External backends are untrusted.
- Lean is the sole authority for theorem acceptance.
- A backend Boolean answer is never sufficient evidence.
- Accepted results must be bound to the exact request by cryptographic digest.
- Offline replay must recheck committed evidence without trusting the solver.

Forensic regressions under `tests/forensic/` guard several of these properties.

---

## Current engineering posture

Wave 0–1 claim correction, Candidate Bundle v0.3, content-addressed store, and
Certification Record verification are present in tree. Wave 2 adds
`mathevidence-kernel-replay` (protocol-reference fixture) plus a Python
generated-module driver that **refuses** `soundness_verified` without Lean.
Mathlib-heavy Checkers/IR compile remains the main local/CI cost center.

| Area | Honest status |
| --- | --- |
| Rational equality | Protocol / semantic-boundary **reference**; `externalSearchEssential: false`. Interactive tactic closes fixtures and supported live certs via `eq_of_proposition` / elaborated `eq_of_replaySound` (`Bridge`; `Tactic/Examples.olean`). Kernel Certified also via `mathevidence-kernel-replay` / `replaySound` (Linux CI authoritative; Windows **required** rsp path). |
| Linear algebra / finite CEX | `LinearAlgebra/Bridge.olean` + `BridgeDet.olean` (general-n inverse; rectangular system/kernel for `n ≠ 0`; general-n det via non-partial fuel `detRats` / Laplace) + Fin-5/6 det examples + rectangular examples + `Counterexample/Bridge.olean`. Kernel-replay fixtures inv/sys/ker/det + nat_eq0/bool_false. Practical det scale: intentional `defaultSizeLimit` (64 entries) — resource policy, not a missing proof. |
| `algebra.formal_rational_calculus` | Formal rational-expression calculus only. Analytic `HasDerivAt` / ODE is separate (`analysis.analytic_calculus`). |
| Ideal membership | Fixed-arity IR + Mathlib `Vector`; Soundness + `mem_span_*_of_check` / `mem_span_triple_of_check` + live Meta (`live_x2_minus_1_span` / `live_xy_span` / `live_xyz_span`) oleans attested. Benchmark: candidate smoke never claims `soundness_verified`; release tier emits Certification Records via OfflineFixtures (`xy`/`x2m1`) + `replaySound` (nightly `benchmarks.yml`). Capability id `algebra.ideal_membership_witness`. External backends discovery-only. External held-out (ME-RV-081) **BLOCKED(human)**. |
| Agent API | Experimental. Public ops use opaque IDs. Certified only via verified Certification Record (`open_certification`). |
| Evidence bundles | Candidate Bundle / Certification Record **v0.3**; placeholders rejected. |
| CI / `just check` | Workflows under `.github/workflows/`. Branch protection enabled on `main` (see [`validation/ci/`](../validation/ci/)). `uv.lock` committed @ `1eb1e15` (ME-RV-070 lock-in-history MET); P0-G remains PARTIAL until push + Actions green. Forensic + rational/analytic kernel-replay self-tests in `lean.yml` (Linux authoritative). Local green `just check` is not promotion evidence. |
| CODEOWNERS | Single-owner incubation stub (`@fraware`). Multi-area dual review is **not** enforceable yet (ME-RV-084 / `admin:org`). |
| Stable promotion | **Blocked** until real-vision acceptance matrix + human gates below close. Mechanical gate: `schemas/promotion-record.schema.json` + `registry/promotions/` (ME-RV-087). Living score: [`TRIPLE_CHECK_GAP_MATRIX.md`](../audits/2026-07-26-real-vision/TRIPLE_CHECK_GAP_MATRIX.md) (`MISSING = 0`). |
| Bundle verifier vs kernel replay | `mathevidence-verify-bundle` → `native_checked` / `checker_accepted` only. `mathevidence-kernel-replay` → fixture `replaySound` + analytic `--self-test-analytic` + Python driver. Windows: `scripts/link_exe_via_rsp.py` required; `smoke_exe` degrades with `replay_dependency_missing`. |
| Foundry Q2 | Redefined to require Certification Record fields; v0.1 corpus is `Q1_checker_preview` (0 Q2). |
| Env import/axiom audits | `mathevidence-import-graph` / `mathevidence-axiom-report` use `Lean.importModules` + `CollectAxioms` (`environmentLevel: true`); regex source scans remain defense-in-depth. |

---

## Open limitations (do not invent closures)

### Human and governance (blocking stable)

| ID | Limitation | Where to record progress |
| --- | --- | --- |
| H-1 | ≥3 external Milestone 0 user confirmations | `docs/validation/user-confirmation.md` (0 completed); index: `docs/validation/human-gates-runbook.md` |
| H-2 | ≥1 external workflow-win confirmation (§21.10) | `docs/validation/workflow-win-log.md`; index: `human-gates-runbook.md` |
| H-3 | Independent domain + trust-model reviews for stable promotion | `docs/validation/review-packets/`, `docs/validation/stable-capability-checklist.md`; index: `human-gates-runbook.md` |
| H-4 | Live federation agreements (≥2 external peers) | `docs/validation/federation-live-checklist.md`, `docs/architecture/federation-agreements.md` (fixture peers only today) |
| H-5 | Studio usability session results (≥3 completed) | `docs/validation/studio/usability/` (0 completed results); index: `human-gates-runbook.md` |
| H-6 | Expert judgments (hypothesis interfaces, conjecture precision, TTP lemma graph) | Unsigned review packets under `docs/validation/review-packets/`; index: `human-gates-runbook.md` |
| H-7 | Real multi-area CODEOWNERS / dual approval | `.github/CODEOWNERS`, `GOVERNANCE.md`, `docs/validation/ci/github_teams_me_rv084.md` |

Wave 8 human scaffolding (still **BLOCKED**; do not invent completions):
ME-RV-081 [`held-out-external-benchmark.md`](../validation/held-out-external-benchmark.md),
ME-RV-082/083 [`federation-live-checklist.md`](../validation/federation-live-checklist.md),
ME-RV-085 [`external-validation-interview.md`](../validation/external-validation-interview.md),
ME-RV-086 [`external-adoption-checklist.md`](../validation/external-adoption-checklist.md).
Full index: [`human-gates-runbook.md`](../validation/human-gates-runbook.md).

### Engineering and product (honest gaps)

| ID | Limitation | Notes |
| --- | --- | --- |
| E-1 | Immutable CI green on a release commit | Workflows exist; attested immutable green is still required before calling engineering gates “complete”. |
| E-2 | Lean toolchain pin | Project remains on the committed `lean-toolchain`; a bump is a deliberate, separately validated change. |
| E-3 | LeanLink native Mathematica bridge | Deferred; live Mathematica transport is `wolframscript` when `MATHEVIDENCE_WOLFRAMSCRIPT` is set. |
| E-4 | Sage rational equality | Declared / placeholder; not advertised as live Agent routing. |
| E-5 | Analytic calculus completeness | `Interpret` + `AnalyticCalculus/Soundness` + `ReplaySound` oleans green; `cert_product` generator + CI `--self-test-analytic`; completeness/uniqueness out of scope; Windows exe link via **required** `scripts/link_exe_via_rsp.py` when Lake 4.14 hits CreateProcess 206. |
| E-6 | Production receipt PKI | Dev keys under `dev/receipt-keys/` are for local experiments only. |
| E-7 | Foundry frontier / funding exits | Trivial tool-selection lift may be measured on a tiny suite; frontier acceleration and maintenance funding remain open. |
| E-8 | Frozen `uv.lock` | **Closed for lock-in-history:** committed @ `1eb1e15`. Remote attested CI freeze remains under P0-G / E-1. |
| E-9 | Signed 0.x prerelease | Provenance/SBOM scaffolding present; signing + human publish approval open (ME-RV-074). |
| E-10 | Environment-level Lean audits | **Closed for ME-RV-071/072** via `importModules` / `CollectAxioms` drivers + CI; keep source-scan as defense-in-depth. |
| E-11 | Ideal flagship adoption | Live Meta + soundness oleans green; in-repo release-grade Certification Record MET (OfflineFixtures). No live external adoption; ME-RV-081 external held-out **BLOCKED(human)**. |
| E-12 | Rational tactic authority | **Closed for supported live fragment:** fixtures + elaborated live `eq_of_replaySound` (`RationalClose.tryCloseViaReplaySoundLive`); non-fixture examples + adversarial rejects in `Tactic/Examples.olean`. Authority remains checker soundness (no independent final `field_simp; ring`). |
| E-13 | LA Bridge det (closed) | General-n `det_of_isDetIdentity` via non-partial `detRatsFuel`; Fin-5/6 examples green. **Intentional resource policy:** factorial Laplace cost + `IR/MatrixExpr.defaultSizeLimit` (64 entries) bound practical `n` — not a missing proof (A5). |
| E-14 | Theorem identity `Expr.hash` | Type + proof-term digests via structural `ExprSerialize` MET; Lean-internal `Expr.hash` across compiler revisions still not claimed (must not be used). |
| E-15 | Windows kernel-replay native Lake link | PARTIAL(toolchain). Required local path: `scripts/link_exe_via_rsp.py`; `smoke_exe` / `just exe-smoke` degrade with `replay_dependency_missing`. Linux CI authoritative. |

---

## Capability naming notes

- Public calculus capability ID: **`algebra.formal_rational_calculus`**.
- Ideal membership capability ID: **`algebra.ideal_membership_witness`**.
- Legacy schema and conformance paths may still use `symbolic_calculus` /
  `calculus` directory names; those are wire/fixture names, not analytic claims.
- Do not advertise a live `analysis.symbolic_calculus` registry ID.

---

## Forensic suite

Trust regressions live under `tests/forensic/`. They assert correct trust
behavior (binding, path rejection, registry/API honesty, and related cases).
A green forensic suite does **not** by itself authorize `"status": "stable"`.
