# Project status (public preview)

**Branch / preview:** `main` public preview (audited head `c7040e6`; living score in [`audits/2026-07-26-real-vision/TRIPLE_CHECK_GAP_MATRIX.md`](audits/2026-07-26-real-vision/TRIPLE_CHECK_GAP_MATRIX.md))  
**Capability status:** all registry capabilities remain **`experimental`**  
**Authoritative limitations:** [`security/KNOWN_TRUST_GAPS.md`](security/KNOWN_TRUST_GAPS.md)  
**Real-vision re-audit (2026-07-26):** [`audits/2026-07-26-real-vision/`](audits/2026-07-26-real-vision/) — living checklist in [`15_ACCEPTANCE_MATRIX.md`](audits/2026-07-26-real-vision/15_ACCEPTANCE_MATRIX.md) (historical `c7040e6` snapshot vs current score); stable promotion stays **blocked**.

This page is the short, honest status for outsiders. Detailed §21 / milestone
mapping lives in [`validation/remaining-spec-matrix.md`](validation/remaining-spec-matrix.md).

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
| Kernel replay (Wave 2) | `mathevidence-kernel-replay` Lake target + rational/analytic fixtures; **Linux CI** `--self-test` + `--self-test-analytic` **authoritative**; Windows **required** path is `scripts/link_exe_via_rsp.py` (also attempted by `just exe-smoke` / `smoke_exe.py`); degrade with `replay_dependency_missing` — never fake Certified (see `KERNEL_REPLAY_PLATFORM.md`); Python timeout → `resource_limit_exceeded` |
| Rational tactic (ME-RV-023) | Fixtures + live elaborated `eq_of_replaySound` Bridge close (`Tactic/Examples.olean` non-fixture + adversarial); not independent `field_simp; ring` |
| Linear algebra det scale | General-n Bridge MET; practical `n` bounded by intentional `IR/MatrixExpr.defaultSizeLimit` (64 entries) + Laplace cost — resource policy, not a missing proof |
| Agent API | **v0.1.0**; open/inspect/replay by opaque **`bundleId` only** (no public path API) |
| Evidence Bundle schema | Candidate Bundle / Certification Record **v0.3**; placeholders removed (ME-RV-002) |
| Calculus capability ID | `algebra.formal_rational_calculus` (formal rational calculus only) |
| Ideal capability ID | `algebra.ideal_membership_witness` |
| Ideal benchmark (P0-F) | Candidate tier MET (smoke/`just check`); release-grade Certification Record MET for in-repo OfflineFixtures path (`--tier release` / nightly); ME-RV-081 external held-out **BLOCKED(human)** |
| CODEOWNERS | Single-owner incubation stub — see `GOVERNANCE.md` (ME-RV-084); team create needs `admin:org` |
| Python lock | `uv.lock` committed @ `1eb1e15` + `uv sync --frozen` in CI (`docs/architecture/python-deps.md`); push/Actions attestation still open (P0-G) |
| Branch protection | Enabled on `main` (2026-07-26); see `docs/validation/ci/2026-07-26_closure_ci_truth.json` |
| Promotion records | `schemas/promotion-record.schema.json` enforced for any future `stable` |

## Not yet

- External library-derived ideal held-out (ME-RV-081) — **BLOCKED(human)**; in-repo
  `held_out` stratum is synthetic. In-repo release-grade Certification Record path
  (P0-F / ME-RV-035 OfflineFixtures) is MET; candidate smoke stays non-certified.
- Full theorem-producing Certification Record closure across **all** capabilities
  (rational + analytic + LA fixtures + Ideal live Meta Fin≤3 / OfflineFixtures are green for their
  owned fragments).
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
| [`audits/2026-07-26-real-vision/`](audits/2026-07-26-real-vision/) | Normative real-vision re-audit + acceptance matrix |
| [`security/KNOWN_TRUST_GAPS.md`](security/KNOWN_TRUST_GAPS.md) | Known limitations / trust gaps |
| [`validation/stable-capability-checklist.md`](validation/stable-capability-checklist.md) | Only path to `stable` |
| [`validation/ci/`](validation/ci/) | Machine-readable CI truth records |
| [`architecture/python-deps.md`](architecture/python-deps.md) | Frozen `uv.lock` policy |
| [`validation/remaining-spec-matrix.md`](validation/remaining-spec-matrix.md) | §21 / milestone honesty matrix |
| [`release/RELEASE_NOTES_DRAFT.md`](release/RELEASE_NOTES_DRAFT.md) | Public-preview release notes draft |
| [`PROJECT_SPEC.md`](PROJECT_SPEC.md) | Normative specification |
| [`README.md`](README.md) | Documentation landing |
