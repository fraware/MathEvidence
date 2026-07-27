# Post-push CI attestation (P0-G remainder)

Prepared: 2026-07-27 (Tier B). **No Actions capture yet** — awaits push.

## Purpose

After the real-vision closure commit is pushed to `origin`, fill
[`POST_PUSH_CI_ATTESTATION_TEMPLATE.json`](POST_PUSH_CI_ATTESTATION_TEMPLATE.json)
(or copy to `<sha7>_ci_truth.json`) with real workflow run IDs.

Until then: local commit SHA + this package only. P0-G stays PARTIAL.

## Required checks (must stay required on `main`)

From [`branch_protection_recommended.json`](branch_protection_recommended.json):

| Context | Must cover |
| --- | --- |
| `lean / lean` | Lake build; kernel-replay `--self-test` + `--self-test-analytic`; forensic (`pytest tests/forensic`); env audits; frozen `uv sync` |
| `offline-replay / offline-replay` | Offline replay; frozen `uv sync` |
| `adapter-conformance / sympy-conformance` | Adapter/schema gates; frozen `uv sync` |
| `adversarial / adversarial-seed` | Adversarial seed; frozen `uv sync` |
| `security / security` | Security/static gates; frozen `uv sync` |
| `supply-chain / gitleaks` | Secret scan |

## Capture commands (after push)

```bash
SHA=$(git rev-parse HEAD)
gh run list --repo fraware/MathEvidence --branch main --commit "$SHA" --limit 20
gh api repos/fraware/MathEvidence/branches/main/protection --jq '.required_status_checks'
# For each required run:
gh run view <run_id> --repo fraware/MathEvidence --json conclusion,name,databaseId,url,headSha
```

Write results into the JSON template fields `localCommit.sha`, `actionRuns.*`,
`branchProtection`, set `status` to `CAPTURED`, and set `recordedAt`.

## Honesty

- Do not invent run IDs.
- Do not claim P0-G MET without green required contexts on protected `main`.
- Stable promotion remains frozen.
