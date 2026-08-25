# Project status (public preview)

**Current assurance semantics (PR #53 / post-repair):** exact candidate binding.
A fixture or nearby theorem cannot certify a different submitted candidate.
`algebra.ideal_membership_witness`, `algebra.rational_equality`,
`algebra.linear_algebra`, `logic.finite_counterexample`,
`algebra.formal_rational_calculus`, and `analysis.analytic_calculus` are
CR-eligible after local Lean exact-replay E2E (`proved` except CEX which is
`refuted`). Federated logic capabilities remain non-eligible. Authority:
[`registry/maturity-inventory.json`](../registry/maturity-inventory.json),
[`adr/0005-exact-candidate-binding.md`](adr/0005-exact-candidate-binding.md),
and [`validation/handoff-2026-08-25-delta.md`](validation/handoff-2026-08-25-delta.md).

**Historical preview snapshot:** `main` public preview (audited head `c7040e6`;
living score in [`audits/2026-07-26-real-vision/TRIPLE_CHECK_GAP_MATRIX.md`](audits/2026-07-26-real-vision/TRIPLE_CHECK_GAP_MATRIX.md)).
Dated `MET` labels in the highlights table, in
[`validation/remaining-spec-matrix.md`](validation/remaining-spec-matrix.md),
and in `audits/2026-07-26-real-vision/` are **historical engineering-artifact
records**. They are not current theorem-level Certification Record authority.

**Capability lifecycle status:** all registry capabilities remain **`experimental`**  
**Authoritative limitations:** [`security/KNOWN_TRUST_GAPS.md`](security/KNOWN_TRUST_GAPS.md)  
**Real-vision re-audit (2026-07-26):** [`audits/2026-07-26-real-vision/`](audits/2026-07-26-real-vision/) — living checklist in [`15_ACCEPTANCE_MATRIX.md`](audits/2026-07-26-real-vision/15_ACCEPTANCE_MATRIX.md) (historical `c7040e6` snapshot vs current score); stable promotion stays **blocked**.

This page is the short, honest status for outsiders. Operator runbook:
[`HANDOFF.md`](HANDOFF.md). Detailed §21 / milestone mapping lives in
[`validation/remaining-spec-matrix.md`](validation/remaining-spec-matrix.md).

## Current assurance maturity (PR #53)

Independent booleans. Checker or fixture existence does not imply exact binding
or Certification Record eligibility. Ideal, rational equality, linear algebra,
finite counterexample, formal rational calculus, and analytic calculus are
currently `cr_eligible=true`; federated logic remains false.

<!-- maturity-inventory-table:begin -->
| Capability | adapter_exists | checker_exists | lean_soundness_exists | bridge_replay_exists | exact_candidate_binding_exists | offline_replay_exists | cr_eligible |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `algebra.ideal_membership_witness` | true | true | true | true | true | true | true |
| `algebra.rational_equality` | true | true | true | true | true | true | true |
| `algebra.linear_algebra` | true | true | true | true | true | true | true |
| `logic.finite_counterexample` | true | true | true | true | true | true | true |
| `algebra.formal_rational_calculus` | true | true | true | true | true | true | true |
| `analysis.analytic_calculus` | true | true | true | true | true | true | true |
| `logic.sat_unsat` | true | false | false | false | false | false | false |
| `logic.pseudo_boolean` | true | false | false | false | false | false | false |
| `logic.smt` | true | false | false | false | false | false | false |
<!-- maturity-inventory-table:end -->

## What this preview is

An **experimental** computational-evidence platform for Lean: protocol,
semantic IR, verified checkers, untrusted adapters, Agent API, Studio surfaces,
registry, Foundry schemas/corpus samples, and offline evidence bundles.

It is **not**:

- a stable computational-evidence layer;
- a claim that human gates (external confirmations, dual-area review, live
  federation, usability studies) are complete;
- attested immutable CI green on a tagged release commit with required checks
  (see [`validation/ci/`](validation/ci/) — branch protection is on; release
  attestation still open);
- a Foundry Q2 formally-verified corpus at scale (v0.1 sample episodes are
  reclassified to `Q1_checker_preview` pending Certification Records).

## Engineering highlights in this preview

| Area | Status |
| --- | --- |
| Request binding / offline digest recompute | Engineering fixes present; guarded by `tests/forensic/` |
| Bundle verification (Wave 0) | `mathevidence-verify-bundle` emits `native_checked` / `checker_accepted` only — **not** theorem Certified |
| Kernel replay (Wave 2) | **PR #53 + exact binding:** theorem CR path is fail-closed except registry `crEligible` capabilities with exact generators (ideal, rational equality, LA, CEX `refuted`, formal/analytic calculus). Rational/analytic OfflineFixtures `--self-test` executables remain **protocol fixtures only**, not Certification Record authority. Windows **required** path is `scripts/link_exe_via_rsp.py`; degrade with `replay_dependency_missing` — never fake Certified (see `KERNEL_REPLAY_PLATFORM.md`) |
| Rational tactic (ME-RV-023) | Fixtures + live elaborated `eq_of_replaySound` Bridge close (`Tactic/Examples.olean` non-fixture + adversarial); not independent `field_simp; ring` |
| Linear algebra det scale | **Historical:** general-n Bridge MET at the 2026-07-26 audit. Practical `n` bounded by intentional `IR/MatrixExpr.defaultSizeLimit` (64 entries) + Laplace cost — resource policy, not a missing proof. **Current:** exact-candidate generator + CR-eligible after Lean E2E for all four ops |
| Agent API | **v0.1.0**; open/inspect/replay by opaque **`bundleId` only** (no public path API) |
| Evidence Bundle schema | Candidate Bundle v0.3; Certification Record **v0.4** for exact promotion (`0.4.0`). Legacy v0.3 records parse under original version and must not be silently upgraded |
| Calculus capability ID | `algebra.formal_rational_calculus` (formal rational calculus only) |
| Ideal capability ID | `algebra.ideal_membership_witness` |
| Ideal benchmark (P0-F) | **Historical (pre-PR #53):** candidate tier MET; release-grade Certification Record MET for in-repo OfflineFixtures. **Current:** OfflineFixtures are protocol self-tests; exact generator + Lean E2E enable `cr_eligible=true` for theorem CR on the submitted candidate. ME-RV-081 external held-out **BLOCKED(human)** |
| CODEOWNERS | Single-owner incubation stub — see `GOVERNANCE.md` (ME-RV-084); team create needs `admin:org` |
| Python lock | `uv.lock` committed @ `1eb1e15` + `uv sync --frozen` in CI (`docs/architecture/python-deps.md`); push/Actions attestation still open (P0-G) |
| Branch protection | Enabled on `main` (2026-07-26); see `docs/validation/ci/2026-07-26_closure_ci_truth.json` |
| Promotion records | `schemas/promotion-record.schema.json` enforced for any future `stable` |

## Not yet

- External library-derived ideal held-out (ME-RV-081) — **BLOCKED(human)**; in-repo
  `held_out` stratum is synthetic. **Historical:** in-repo OfflineFixtures
  release-grade path was recorded MET before PR #53. **Current:** fixture replay
  does not authorize a Certification Record; candidate smoke stays non-certified.
- Theorem-producing Certification Record eligibility across **all** capabilities
  (`cr_eligible` false for federated logic). Owned exact-bound capabilities are
  CR-eligible after Lean E2E; federated SAT/PB/SMT stay fail-closed.
- Live federation with external projects (fixtures only; templates under `.github/ISSUE_TEMPLATE/`).
- Human gates: external confirmations, expert signatures, Studio session results, adoption.
- Signed 0.x experimental GitHub prerelease (pipeline wired; human publish gated — see `validation/ci/signed_0x_prerelease.md`).
- Org maintainer teams for multi-area CODEOWNERS (needs `admin:org` — see `validation/ci/github_teams_me_rv084.md`).
- Push of local closure commits (`1eb1e15` / `c1c3303`) + attested Actions green on protected main (P0-G); see `validation/ci/post_push_ci_attestation.md`.
- Native Lake Windows link for `mathevidence-kernel-replay` without rsp (PARTIAL toolchain; rsp is the supported local path).
- `"status": "stable"` on any capability — **frozen**; mechanically blocked without promotion record.
- Production receipt PKI.
- Lean-internal `Expr.hash` across compiler revisions (structural `ExprSerialize` type + proof-term digests are in place and do not use `Expr.hash`).


## How to build and test

See [`getting-started/`](getting-started/) and the root
[`README.md`](../README.md). Typical local gate: `just check` (Lean build,
schema/registry validation, Python tests, conformance, replay, exe smoke,
ideal-membership smoke, forensic, Foundry validate). Forensic subset:

```text
pytest tests/forensic -q
```

Workflow definitions: `.github/workflows/`. Do not treat local green alone as
promotion evidence.

## Related docs

| Doc | Role |
| --- | --- |
| [`HANDOFF.md`](HANDOFF.md) | Engineering handoff / operational runbook |
| [`adr/0005-exact-candidate-binding.md`](adr/0005-exact-candidate-binding.md) | Exact-candidate-binding invariant (PR #53) |
| [`validation/handoff-2026-08-25-delta.md`](validation/handoff-2026-08-25-delta.md) | Workspace SHA vs handoff pin + Lean CI diagnostic |
| [`../registry/maturity-inventory.json`](../registry/maturity-inventory.json) | Machine-readable capability maturity / CR eligibility |
| [`audits/2026-07-26-real-vision/`](audits/2026-07-26-real-vision/) | Historical real-vision re-audit + acceptance matrix (not current CR authority) |
| [`security/KNOWN_TRUST_GAPS.md`](security/KNOWN_TRUST_GAPS.md) | Known limitations / trust gaps |
| [`validation/stable-capability-checklist.md`](validation/stable-capability-checklist.md) | Only path to `stable` |
| [`validation/ci/`](validation/ci/) | Machine-readable CI truth records |
| [`architecture/python-deps.md`](architecture/python-deps.md) | Frozen `uv.lock` policy |
| [`validation/remaining-spec-matrix.md`](validation/remaining-spec-matrix.md) | §21 / milestone honesty matrix |
| [`release/RELEASE_NOTES_DRAFT.md`](release/RELEASE_NOTES_DRAFT.md) | Public-preview release notes draft |
| [`PROJECT_SPEC.md`](PROJECT_SPEC.md) | Normative specification |
| [`README.md`](README.md) | Documentation landing |
