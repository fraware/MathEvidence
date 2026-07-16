# Library contribution tracking template

Use one row (or one YAML block) per measured downstream contribution.
Do **not** mark Milestone 6 exit criteria closed without merged evidence.

## Spreadsheet / table form

| Field | Value |
| --- | --- |
| contribution_id | (uuid or short slug) |
| date | YYYY-MM-DD |
| target_library | e.g. mathlib4 / project name |
| target_repo_url | https://... |
| pr_or_commit_url | https://... |
| status | proposed / under_review / merged / rejected |
| declaration_names | `Foo.bar`, `...` |
| capability_id | e.g. `algebra.rational_equality` |
| request_digest | `sha256:...` |
| evidence_bundle_path | `evidence/...` or external URI |
| assurance_mode | `kernel_replay` / ... |
| claim_class | |
| result_status | |
| foundry_episode_id | (optional; never used for acceptance) |
| human_reviewer | |
| hours_saved_estimate | number or `unknown` |
| notes | |

## YAML form

```yaml
contribution_id: example-0001
date: 2026-07-16
target_library: example-lib
target_repo_url: https://example.invalid/org/repo
pr_or_commit_url: https://example.invalid/org/repo/pull/0
status: proposed
declaration_names: []
capability_id: algebra.rational_equality
request_digest: sha256:0
evidence_bundle_path: evidence/examples/rational_equality_basic
assurance_mode: kernel_replay
claim_class: soundResult
result_status: certified
foundry_episode_id: null
human_reviewer: null
hours_saved_estimate: unknown
notes: >
  Template only. Replace with real collaboration records.
  Foundry episode ids are diagnostic; they must not influence acceptance.
```

## Aggregation rules

- Count **merged** contributions separately from proposed ones.
- Do not double-count rebased PRs.
- Federated capabilities credit the external checker owner for proof authority;
  MathEvidence credits metadata / packaging only.
- Material acceleration claims require at least one merged contribution **and**
  a written note from a collaboration contact (external exit criterion).

## Storage

Committed templates and anonymized aggregates may live under
`docs/foundry/contributions/`. Private collaboration details stay off-repo.
