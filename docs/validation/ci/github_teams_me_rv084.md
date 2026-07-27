# GitHub maintainer teams (ME-RV-084)

Recorded: 2026-07-26  
Re-attempted: 2026-07-27 (Tier B / close-remaining-gaps)

## Attempt result — BLOCKED

Creating org teams under `fraware` requires the `admin:org` OAuth scope.
Current `gh auth status` token scopes (2026-07-27):

```text
gist, read:org, repo, user, workflow
```

Commands attempted (both dates; same outcome):

```text
gh api orgs/fraware/teams
# HTTP 404 Not Found

gh api -X POST orgs/fraware/teams \
  -f name="Core/trust" -f privacy=closed \
  -f description="Core and trust-path maintainers"
# HTTP 404 Not Found
# (GitHub hides org-admin failures as 404 without admin:org)

gh api user/memberships/orgs/fraware
# HTTP 404 — needs: gh auth refresh -h github.com -s admin:org
```

**Status:** BLOCKED. Teams were **not** created. `.github/CODEOWNERS` remains the
single-owner `@fraware` incubation stub. Do **not** substitute invented
`@fraware/<slug>` entries until teams exist and membership is real.

## Maintainer commands (org admin)

Refresh auth, then create the eight teams:

```bash
gh auth refresh -h github.com -s admin:org

gh api -X POST orgs/fraware/teams -f name="Core/trust" -f privacy=closed \
  -f description="Core and trust-path maintainers"
gh api -X POST orgs/fraware/teams -f name="Semantic IR/encoding" -f privacy=closed \
  -f description="Semantic IR and encoding maintainers"
gh api -X POST orgs/fraware/teams -f name="Domain checkers" -f privacy=closed \
  -f description="Domain checker and tactic maintainers"
gh api -X POST orgs/fraware/teams -f name="Adapters" -f privacy=closed \
  -f description="Backend adapter maintainers"
gh api -X POST orgs/fraware/teams -f name="Agent/Studio" -f privacy=closed \
  -f description="Agent API and Studio maintainers"
gh api -X POST orgs/fraware/teams -f name="Foundry/benchmarks" -f privacy=closed \
  -f description="Foundry and benchmark maintainers"
gh api -X POST orgs/fraware/teams -f name="Security/release" -f privacy=closed \
  -f description="Security, CI, and release maintainers"
gh api -X POST orgs/fraware/teams -f name="Docs/governance" -f privacy=closed \
  -f description="Docs, registry, and governance maintainers"
```

Expected slugs (verify with `gh api orgs/fraware/teams --jq '.[].slug'`):

| Area | Expected slug |
| --- | --- |
| Core/trust | `core-trust` |
| Semantic IR/encoding | `semantic-ir-encoding` |
| Domain checkers | `domain-checkers` |
| Adapters | `adapters` |
| Agent/Studio | `agent-studio` |
| Foundry/benchmarks | `foundry-benchmarks` |
| Security/release | `security-release` |
| Docs/governance | `docs-governance` |

Add the publishing user (and future maintainers) to each team, then substitute
`@fraware/<slug>` into `.github/CODEOWNERS` (path layout is already ready;
section headers name the target slug).

Verify membership before enabling dual-area review:

```bash
gh api orgs/fraware/teams --jq '.[].slug'
# for each slug:
gh api orgs/fraware/teams/<slug>/members --jq '.[].login'
```

## Honesty

Until distinct humans own distinct teams, dual-area CODEOWNERS review is not
independent-area governance. Stable promotion remains blocked.
