# Governance

MathEvidence is governed as shared formal-mathematics infrastructure.

## Maintainer areas (target)

| Area | Intended GitHub team stub | Primary paths |
| --- | --- | --- |
| Core and trust model | `@fraware/core-trust` | `MathEvidence/Core`, schemas, security |
| Semantic IR / encoding | `@fraware/semantic-ir-encoding` | `MathEvidence/IR`, `Encoding` |
| Domain checkers | `@fraware/domain-checkers` | `MathEvidence/Checkers`, `Tactic` |
| Backend adapters | `@fraware/adapters` | `adapters/` |
| Agent API + Studio | `@fraware/agent-studio` | `agent/`, `studio/` |
| Foundry and benchmarks | `@fraware/foundry-benchmarks` | `foundry/`, `benchmarks/` |
| Security and releases | `@fraware/security-release` | workflows, CI truth, release |
| Docs and governance | `@fraware/docs-governance` | `docs/`, `GOVERNANCE.md`, registry |

Stable protocol changes require two approvals from different areas. Domain
semantics require relevant mathematical expertise. No single maintainer may
unilaterally weaken replay, axiom, request-binding, or claim-strength
guarantees.

## Current incubation reality (ME-RV-084)

`.github/CODEOWNERS` is a **single-owner stub** (`@fraware` on all paths).
Real GitHub teams require **org admin** action and do not exist yet. Path
structure and team handle stubs are ready for substitution; substituting the
same person into multiple teams does **not** satisfy independent-area review
for stable promotion.

Until real teams exist:

- all capabilities remain `"experimental"`;
- stable promotion remains blocked by
  [`docs/validation/stable-capability-checklist.md`](docs/validation/stable-capability-checklist.md),
  [`schemas/promotion-record.schema.json`](schemas/promotion-record.schema.json),
  and human gates in
  [`docs/security/KNOWN_TRUST_GAPS.md`](docs/security/KNOWN_TRUST_GAPS.md);
- trust-model or checker weakenings still require explicit scrutiny even if
  GitHub cannot yet enforce two distinct area teams.

## Capability status

Registry `"status": "stable"` is a governance event, not a documentation edit.
`scripts/validate_registry.py` refuses `stable` without a schema-valid signed
promotion record under `registry/promotions/`. Engineering packaging and green
local `just check` are insufficient without checklist artifacts (external
confirmations, review packets, and CI evidence).

## Branch protection

As of 2026-07-26 closure, `main` **is** branch-protected (required PR + required
checks + code-owner review). Evidence:
[`docs/validation/ci/2026-07-26_closure_ci_truth.json`](docs/validation/ci/2026-07-26_closure_ci_truth.json).
Org maintainer teams (ME-RV-084) still require `admin:org` — see
[`docs/validation/ci/github_teams_me_rv084.md`](docs/validation/ci/github_teams_me_rv084.md).
