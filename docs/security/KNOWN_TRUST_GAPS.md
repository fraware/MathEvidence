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

Exact candidate binding is required for theorem-level Certification Records
([ADR 0005](../adr/0005-exact-candidate-binding.md)). Live CR eligibility is
registry-backed ([`docs/STATUS.md`](../STATUS.md),
[`registry/maturity-inventory.json`](../../registry/maturity-inventory.json)).
OfflineFixtures and checker-only green are **not** CR authority for a submitted
candidate. Mathlib-heavy Checkers/IR compile remains the main local/CI cost center.

| Area | Honest status |
| --- | --- |
| Exact binding / CR | Six owned capabilities are `cr_eligible=true` after Lean exact-replay E2E (`proved`, except CEX `refuted`). Federated SAT/PB/SMT never CR-eligible under exact binding. |
| Rational equality | Protocol / semantic-boundary **reference**; interactive tactic closes fixtures and supported live certs via `eq_of_proposition` / `eq_of_replaySound`. Exact generator + CR path when registry allows. Linux CI authoritative for linked exe; Windows **required** rsp path. |
| Linear algebra / finite CEX | Bridge + exact generators for registered ops; practical det scale bounded by intentional `defaultSizeLimit` (64 entries). CEX CR outcome is `refuted` only. |
| Formal / analytic calculus | `algebra.formal_rational_calculus` is formal/algebraic only. `analysis.analytic_calculus` is a separate whitelist; exact ODE requires empty domain obligations and at most one initial condition. |
| Ideal membership | Witness identity only (`algebra.ideal_membership_witness`); no Groebner / non-membership completeness. Exact generator + CR path when registry allows. OfflineFixtures remain protocol self-tests. External held-out (ME-RV-081) **BLOCKED(human)**. |
| Agent API | Experimental. Public ops use opaque IDs. Certified only via verified Certification Record (`open_certification`). |
| Evidence bundles | Candidate Bundle **v0.3**; Certification Record **v0.4** for exact promotion. Legacy v0.3 must not be silently upgraded. Placeholders rejected. |
| Offline exact inspect | Defaults to `theorem_pending`; `MATHEVIDENCE_OFFLINE_LEAN=1` / `require_lean=True` may yield `theorem_proved` when Lake is available — still not a CR mint. |
| CI / `just check` | Workflows under `.github/workflows/`. Branch protection enabled on `main` (see [`validation/ci/`](../validation/ci/)). Local green `just check` is not promotion evidence or attested release CI. |
| CODEOWNERS | Single-owner incubation stub (`@fraware`). Multi-area dual review is **not** enforceable yet (ME-RV-084 / `admin:org`). |
| Stable promotion | **Blocked** until acceptance matrix + human gates below close. Mechanical gate: `schemas/promotion-record.schema.json` + `registry/promotions/`. Historical scoreboard: [`TRIPLE_CHECK_GAP_MATRIX.md`](../audits/2026-07-26-real-vision/TRIPLE_CHECK_GAP_MATRIX.md). |
| Bundle verifier vs kernel replay | `mathevidence-verify-bundle` → `native_checked` / `checker_accepted` only. Exact theorem path uses declaration-identity + registry policy. Windows: `scripts/link_exe_via_rsp.py` required; degrade with `replay_dependency_missing` — never fake Certified. |
| Signing / PKI | Production receipt PKI and signed 0.x prerelease attestation remain **deferred** (dev keys under `dev/receipt-keys/` only). |
| Foundry Q2 | Redefined to require Certification Record fields; v0.1 corpus is `Q1_checker_preview` (0 Q2). |
| Env import/axiom audits | `mathevidence-import-graph` / `mathevidence-axiom-report` use `Lean.importModules` + `CollectAxioms`; regex source scans remain defense-in-depth. |

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
| E-11 | Ideal flagship adoption | Exact CR path exists for witness identity when registry `crEligible`. OfflineFixtures are not CR authority for a submitted candidate. No live external adoption; ME-RV-081 external held-out **BLOCKED(human)**. |
| E-12 | Rational tactic authority | **Closed for supported live fragment:** fixtures + elaborated live `eq_of_replaySound` (`RationalClose.tryCloseViaReplaySoundLive`); non-fixture examples + adversarial rejects in `Tactic/Examples.olean`. Authority remains checker soundness (no independent final `field_simp; ring`). |
| E-13 | LA Bridge det (closed) | General-n `det_of_isDetIdentity` via non-partial `detRatsFuel`; Fin-5/6 examples green. **Intentional resource policy:** factorial Laplace cost + `IR/MatrixExpr.defaultSizeLimit` (64 entries) bound practical `n` — not a missing proof (A5). |
| E-14 | Theorem identity `Expr.hash` | Type + proof-term digests via structural `ExprSerialize` MET; Lean-internal `Expr.hash` across compiler revisions still not claimed (must not be used). |
| E-15 | Windows kernel-replay native Lake link | PARTIAL(toolchain). Required local path: `scripts/link_exe_via_rsp.py`; `smoke_exe` / `just exe-smoke` degrade with `replay_dependency_missing`. Linux CI authoritative. |

---

## Capability naming notes

- Public calculus capability ID: **`algebra.formal_rational_calculus`**.
- Analytic calculus capability ID: **`analysis.analytic_calculus`** (separate;
  whitelist only; exact ODE empty-obligation single-IC).
- Ideal membership capability ID: **`algebra.ideal_membership_witness`**.
- Legacy schema and conformance paths may still use `symbolic_calculus` /
  `calculus` directory names; those are wire/fixture names, not analytic claims.
- Do not advertise a live `analysis.symbolic_calculus` registry ID.

---

## Forensic suite

Trust regressions live under `tests/forensic/`. They assert correct trust
behavior (binding, path rejection, registry/API honesty, and related cases).
A green forensic suite does **not** by itself authorize `"status": "stable"`.
