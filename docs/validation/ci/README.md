# CI truth records

Machine-readable CI / branch-protection snapshots for release honesty.

| Record | Notes |
| --- | --- |
| [`c7040e6_wave0_ci_truth.json`](c7040e6_wave0_ci_truth.json) | Wave 0: Actions green for audited head; `main` was **not** protected. |
| [`wave7_scaffold_ci_truth.json`](wave7_scaffold_ci_truth.json) | Wave 7 scaffold gaps (historical). |
| [`2026-07-26_closure_ci_truth.json`](2026-07-26_closure_ci_truth.json) | Closure pass: branch protection **enabled**; elan checksum-pinned; `uv.lock` in tree; Mathlib pin verified locally. |
| [`POST_PUSH_CI_ATTESTATION_TEMPLATE.json`](POST_PUSH_CI_ATTESTATION_TEMPLATE.json) | Tier B template: required-check map + empty run IDs; fill after push. |
| [`post_push_ci_attestation.md`](post_push_ci_attestation.md) | Human runbook for post-push Actions capture (P0-G remainder). |
| [`branch_protection_recommended.json`](branch_protection_recommended.json) | Settings JSON applied (and re-applicable) via `gh api`. |
| [`github_teams_me_rv084.md`](github_teams_me_rv084.md) | Org-team creation **BLOCKED** without `admin:org` (re-attempted 2026-07-27). |
| [`signed_0x_prerelease.md`](signed_0x_prerelease.md) | Complete 0.x signed prerelease runbook; no publish / no tag push claimed. |

Do not treat local `just check` or non-required workflow successes as stable-promotion evidence. Stable remains frozen.
