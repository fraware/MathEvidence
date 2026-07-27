# Human gates runbook (H-1 … H-7 + ME-RV-081…086)

Index of **fillable** packages for human / external / governance gates.
Engineering packaging does **not** close any row below.

**Honesty rule:** every gate stays **BLOCKED** / **OPEN** until a real artifact
exists. Zero invented completions. Gap matrix must not mark MET for these rows.

Canonical status table: `docs/security/KNOWN_TRUST_GAPS.md`.

## ME-RV Wave 8 human package

| ID | Status | Fillable package | GitHub |
| --- | --- | --- | --- |
| ME-RV-081 | **BLOCKED(human)** — 0/20 slots | [`held-out-external-benchmark.md`](held-out-external-benchmark.md) | [#43](https://github.com/fraware/MathEvidence/issues/43) |
| ME-RV-082 | **BLOCKED(human)** — fixture_only | [`federation-live-checklist.md`](federation-live-checklist.md) | [#44](https://github.com/fraware/MathEvidence/issues/44) |
| ME-RV-083 | **BLOCKED(human)** — fixture_only | [`federation-live-checklist.md`](federation-live-checklist.md) | [#45](https://github.com/fraware/MathEvidence/issues/45) |
| ME-RV-084 | **BLOCKED(org)** — single-owner CODEOWNERS | [`ci/github_teams_me_rv084.md`](ci/github_teams_me_rv084.md), `GOVERNANCE.md` | [#46](https://github.com/fraware/MathEvidence/issues/46) |
| ME-RV-085 | **BLOCKED(human)** — 0/3 interviews | [`external-validation-interview.md`](external-validation-interview.md) | [#47](https://github.com/fraware/MathEvidence/issues/47) |
| ME-RV-086 | **BLOCKED(human)** — 0 adoptions | [`external-adoption-checklist.md`](external-adoption-checklist.md) | [#48](https://github.com/fraware/MathEvidence/issues/48) |

Issue forms (do not fake completion):

- `.github/ISSUE_TEMPLATE/held_out_benchmark.yml`
- `.github/ISSUE_TEMPLATE/federation_peer.yml`
- `.github/ISSUE_TEMPLATE/external_validation.yml`
- `.github/ISSUE_TEMPLATE/external_adoption.yml`

## H-gates (stable promotion blockers)

| ID | Limitation | Status | Where to record progress |
| --- | --- | --- | --- |
| H-1 | ≥3 external Milestone 0 user confirmations | **OPEN** — 0 completed | [`user-confirmation.md`](user-confirmation.md), [`outreach-checklist.md`](outreach-checklist.md) |
| H-2 | ≥1 external workflow-win confirmation (§21.10) | **OPEN** — 0 entries | [`workflow-win-log.md`](workflow-win-log.md) |
| H-3 | Independent domain + trust-model reviews | **OPEN** — unsigned templates only | [`review-packets/`](review-packets/), [`stable-capability-checklist.md`](stable-capability-checklist.md), [`expert-review-rubric.md`](expert-review-rubric.md) |
| H-4 | Live federation agreements (≥2 external peers) | **OPEN** — fixture peers only | [`federation-live-checklist.md`](federation-live-checklist.md), `docs/architecture/federation-agreements.md` |
| H-5 | Studio usability session results (≥3 completed) | **OPEN** — protocol ready, 0 results | [`studio/usability/PROTOCOL.md`](studio/usability/PROTOCOL.md), [`studio/usability/sessions/`](studio/usability/sessions/) |
| H-6 | Expert judgments (hypothesis / conjecture / TTP) | **OPEN** — unsigned packets only | [`review-packets/`](review-packets/) (`*-unsigned.md`) |
| H-7 | Real multi-area CODEOWNERS / dual approval | **OPEN** — needs `admin:org` | `.github/CODEOWNERS`, `GOVERNANCE.md`, [`ci/github_teams_me_rv084.md`](ci/github_teams_me_rv084.md) |

## Exit criterion for this package (scaffolding only)

- [x] Fillable templates exist under `docs/validation/`
- [x] GitHub issues opened or updated with package links
- [ ] Any H-gate or ME-RV-081…086 marked MET — **forbidden** until real artifacts

This runbook’s scaffolding checkboxes above are the only ones that may be
ticked by engineering. All human acceptance boxes in linked files stay empty.
