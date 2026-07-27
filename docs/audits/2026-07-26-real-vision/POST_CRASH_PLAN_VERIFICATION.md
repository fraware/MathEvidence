# Post-crash plan verification — real-vision gap closure

**Date:** 2026-07-27  
**Plan:** `c:\Users\mateo\.cursor\plans\close_remaining_gaps_86c1f516.plan.md` (not edited)  
**Scorecard:** [`TRIPLE_CHECK_GAP_MATRIX.md`](TRIPLE_CHECK_GAP_MATRIX.md)  
**Repo:** `c:\Users\mateo\MathEvidence`  
**Method:** File + commit evidence for every A1–A6 / Tier B / Tier C exit criterion; classify DONE / PARTIAL / MISSING; fix only code-fixable honesty drift; no push; no human/org BLOCKED→MET.

---

## Git state (verified)

| Fact | Evidence |
| --- | --- |
| Tip | `c1c3303f440049ec369f984f2686b1c2dad1afd5` — *Record local CI truth stub for closure commit.* |
| Closure | `1eb1e153f681dd2d0fead58330b3d23adf568b87` — *Lock real-vision closure and frozen uv deps into history.* |
| Base on remote | `c7040e6` (origin/main) |
| Ahead of origin | **2 commits**; **not pushed** |
| `uv.lock` | Tracked; introduced/locked in `1eb1e15` (`git ls-files uv.lock`) |
| Tree at tip | Was clean after `c1c3303` |
| Post-verify working tree | Dirty with scorecard honesty fixes + this report (uncommitted; no push) |

---

## Executive: DONE vs leftover

### Truly DONE (plan engineering exits)

| Section | Verdict | Key evidence |
| --- | --- | --- |
| **A1** Live rational Bridge | **DONE** | `RationalClose.tryCloseWithLiveReplaySound` / `tryCloseViaReplaySoundLive` apply `eq_of_replaySound` on elaborated live req/cert; `Discovery.emitLiveRationalArtifacts`; non-fixture `close_live_*` + adversarial in `Tactic/Examples.lean` / Bridge; E-12 closed in KNOWN_TRUST_GAPS |
| **A2** Ideal bench → Cert Record | **DONE** | `--tier candidate\|release` in `run_ideal_membership_benchmark.py`; candidate strips/`refuse` `soundness_verified`; release uses Ideal `OfflineFixtures` (`xy`/`x2m1`); nightly `benchmarks.yml` sets `MATHEVIDENCE_IDEAL_BENCH_TIER=release` |
| **A3** Windows rsp required | **DONE** | `KERNEL_REPLAY_PLATFORM.md` + README + getting-started; `smoke_exe.py` always attempts rsp on Windows; degrade `replay_dependency_missing`; Linux `lean.yml` `--self-test` + `--self-test-analytic` |
| **A5** LA det size policy | **DONE** | Documented intentional `defaultSizeLimit` / Laplace in `docs/assurance/linear-algebra.md`, STATUS, KNOWN_TRUST_GAPS E-13, scorecard ME-RV-040 (optional forensic not required for MET) |
| **A6** Commit + CI truth stub | **DONE** | `1eb1e15` includes `uv.lock` + full closure tree; `c1c3303` adds `docs/validation/ci/1eb1e15…_ci_truth_local.json`; not pushed |
| **Tier B package** | **DONE** (prep only) | Teams BLOCKED docs; signed_0x runbook (no fake publish); post-push attestation template |
| **Tier C package** | **DONE** (scaffolding only) | Held-out / federation / interview / adoption / human-gates templates; all stay **BLOCKED** |

### Leftover (honest; not plan failures)

| Item | Class | Notes |
| --- | --- | --- |
| Push + Actions attestation | **PARTIAL** (P0-G / ME-RV-073) | Intentional; plan forbids push |
| Signed 0.x prerelease publish | **BLOCKED(human)** | Runbook only |
| Org teams / CODEOWNERS multi-area | **BLOCKED(org)** | Needs `admin:org` |
| ME-RV-081…086 + H-1…H-7 | **BLOCKED(human)** | Templates only — correctly not MET |
| Windows native Lake link | **PARTIAL(toolchain)** | rsp required; Linux CI authoritative |
| Optional LA size-limit forensic | skipped | Plan marked optional |
| Scorecard honesty drift after `1eb1e15` | **FIXED this pass** | Docs still claimed `uv.lock` uncommitted / P0-F PARTIAL; corrected in working tree (uncommitted) |

### MISSING

**None.** Executive `MISSING = 0` is honest.

---

## Per-section classification

### A1 — Live rational Bridge (ME-RV-023 / E-12) → **DONE**

| Criterion | Status | Evidence |
| --- | --- | --- |
| Live Meta `eq_of_replaySound` (not fixture-only) | DONE | `MathEvidence/Tactic/RationalClose.lean` `tryCloseWithLiveReplaySound` quotes req/cert + `mkAppM ``eq_of_replaySound`; `tryCloseViaReplaySoundLive` falls through to live after fixture digest miss |
| Discovery Candidate Bundle + Certification Record | DONE | `Discovery.emitLiveRationalArtifacts` + call site after live Bridge close |
| ≥1 non-fixture example + adversarial | DONE | `close_live_add0` / `close_live_cancel`; wrong digest / missing denom / unsupported syntax in `Tactic/Examples.lean` |
| Authority = checker soundness | DONE | Comments + path forbid independent final `field_simp; ring` |
| Scorecard E-12 | DONE | MET for supported live fragment |

**Commit:** present in `1eb1e15`.

### A2 — Ideal benchmark Certification Record (P0-F / ME-RV-035) → **DONE**

| Criterion | Status | Evidence |
| --- | --- | --- |
| `--tier release` + OfflineFixtures Cert Record | DONE | `scripts/run_ideal_membership_benchmark.py` `_release_grade_cert`; fixtures `replay_xy` / `replay_x2m1` |
| `--tier candidate` never `soundness_verified` | DONE | Candidate smoke statuses + strip/refuse if minted |
| Nightly wire | DONE | `.github/workflows/benchmarks.yml` release tier assert |
| Smoke stays candidate | DONE | `lean.yml` / `smoke_ideal_membership.py` |
| External held-out | BLOCKED(human) | Correctly not MET |

**Commit:** `1eb1e15`.

### A3 — Windows rsp hardening → **DONE** (residual PARTIAL toolchain)

| Criterion | Status | Evidence |
| --- | --- | --- |
| Documented required Windows path | DONE | `KERNEL_REPLAY_PLATFORM.md`, README, getting-started |
| `smoke_exe` / `just exe-smoke` rsp attempt | DONE | `scripts/smoke_exe.py` |
| Degrade never fake Certified | DONE | `replay_dependency_missing` |
| Linux CI authoritative | DONE | `lean.yml` self-tests |
| Native Lake Windows MET claim | forbidden | Correctly PARTIAL(toolchain) only |

### A4 — Docs honesty + scorecard sync → **DONE** after this pass (was PARTIAL)

| Criterion | Pre-crash tip | Post-fix |
| --- | --- | --- |
| `15_ACCEPTANCE_MATRIX` historical vs living | Split present | Living checkboxes reconciled (P0-F + uv.lock) |
| MISSING count honest | 0 with note | Unchanged / reaffirmed |
| STATUS / KNOWN_TRUST_GAPS vs A1–A3 | Mostly aligned; **uv.lock stale** | Fixed: lock-in-history MET @ `1eb1e15`; P0-G still PARTIAL |
| TRIPLE_CHECK top gaps | Claimed uv.lock uncommitted + P0-F PARTIAL | Corrected; MET 65 / PARTIAL 6 / MISSING 0 / BLOCKED 12 |

**Crash residue:** scorecards shipped inside `1eb1e15` still said lock “not committed” — self-inconsistent with that commit. Fixed in working tree; **not yet committed**.

### A5 — LA det size limit → **DONE**

Documented intentional resource policy (`defaultSizeLimit` 64 + Laplace). Optional adversarial forensic absent — not required for MET.

### A6 — Full-tree commit + uv.lock (no push) → **DONE**

| Criterion | Status | Evidence |
| --- | --- | --- |
| `uv.lock` in history | DONE | `1eb1e15` |
| CI truth stub | DONE | `c1c3303` → `…1eb1e15…_ci_truth_local.json` awaiting push |
| Not pushed | DONE | ahead 2 |
| Clean tree at tip | DONE at `c1c3303`; dirty after honesty fixes + this report |

### Tier B — Maintainer / org package → **DONE** (execute where gh permits = BLOCKED)

| Item | Verdict | Evidence |
| --- | --- | --- |
| B1 Teams + CODEOWNERS | BLOCKED(org) package DONE | `docs/validation/ci/github_teams_me_rv084.md` records failed `admin:org`; CODEOWNERS stays `@fraware` |
| B2 Signed 0.x | Prep DONE; publish BLOCKED | `signed_0x_prerelease.md` — no fake publish |
| B3 Post-push attestation | Template DONE | `post_push_ci_attestation.md` + `POST_PUSH_CI_ATTESTATION_TEMPLATE.json` (SHA filled this pass; Actions IDs null) |

### Tier C — Human / external gates → **DONE** (scaffolding; rows stay BLOCKED)

| ID | Package | Status row |
| --- | --- | --- |
| ME-RV-081 | `held-out-external-benchmark.md` (0/20) | BLOCKED(human) |
| ME-RV-082/083 | `federation-live-checklist.md` + agreement template | BLOCKED(human) |
| ME-RV-085 | `external-validation-interview.md` (0/3) | BLOCKED(human) |
| ME-RV-086 | `external-adoption-checklist.md` (0) | BLOCKED(human) |
| H-1…H-7 | `human-gates-runbook.md` | OPEN / BLOCKED — not MET |

Exit criterion satisfied: clearer runbooks; **no MET** on human rows.

---

## Plan todos vs reality

| Todo id | Plan YAML status | Truly satisfied? |
| --- | --- | --- |
| `a1-rational-live-bridge` | completed | **Yes** |
| `a2-ideal-bench-cert` | completed | **Yes** |
| `a3-windows-rsp` | completed | **Yes** |
| `a4-docs-scorecard` | completed | **Yes after this fix** (was honesty-stale at tip) |
| `a6-commit-full-tree` | completed | **Yes** (commits exist; tip was clean; new doc fixes uncommitted) |
| `tier-b-org-package` | completed | **Yes** (package only; org/publish still BLOCKED) |
| `tier-c-human-package` | completed | **Yes** (scaffolding; gates BLOCKED) |

---

## Fixes applied this verification (uncommitted)

1. `TRIPLE_CHECK_GAP_MATRIX.md` — executive counts/top gaps; P0-G; ME-RV-003/070/073; reproducibility.
2. `15_ACCEPTANCE_MATRIX.md` — living P0-F checkbox; uv.lock + ideal nightly security rows; CI/repro gates.
3. `docs/STATUS.md` — Python lock / “Not yet” push attestation.
4. `docs/security/KNOWN_TRUST_GAPS.md` — CI/`uv.lock` and E-8 closed for lock-in-history.
5. `docs/validation/ci/POST_PUSH_CI_ATTESTATION_TEMPLATE.json` — real local SHAs; issues → P0-G/ME-RV-073.
6. This file.

**Not done:** commit of the above; push; Actions capture; any BLOCKED→MET.

---

## Verdict

Tier A engineering exits and Tier B/C packages from the plan are **substantively complete** at commits `1eb1e15` + `c1c3303`. The only post-crash unfinished engineering residue was **scorecard/docs honesty lagging the lock commit** — corrected in the working tree. Remaining open items are the intentional leftovers: **no push**, **P0-G attestation**, **org/human BLOCKED gates**, and **Windows native Lake PARTIAL(toolchain)**.
