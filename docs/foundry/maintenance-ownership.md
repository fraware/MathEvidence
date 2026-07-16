# Maintenance funding and ownership plan

Status: **plan artifact for Milestone 6**. This document does **not** assert that
maintenance funding has been secured or that long-term ownership contracts are
signed.

## Goals

Keep MathEvidence trustworthy and operable after the initial delivery milestones:

1. Preserve the trust boundary (adapters / Foundry never enter the theorem TCB).
2. Maintain offline replay, conformance, and adversarial gates in CI.
3. Curate Foundry releases with provenance, quality tiers, and contamination controls.
4. Respond to security reports and capability regressions.

## Ownership map

| Surface | Primary owner role | Backup | Notes |
| --- | --- | --- | --- |
| Lean Core / IR / Checkers | Core maintainers | Domain checker owners | CODEOWNERS for `MathEvidence/Core`, `IR`, `Checkers` |
| Adapters | Adapter maintainers | Core (protocol only) | Untrusted; conformance-owned |
| Registry | Registry maintainers | Core | Schema + status gates |
| Agent API | Agent maintainers | Core | Operation-level tools only |
| Studio | Studio maintainers | Agent | Presentation; no unique semantics |
| Foundry | Foundry maintainers | Benchmarks owners | Post-acceptance only |
| Benchmarks | Benchmarks owners | Foundry | Immutable splits |
| Security / trust model | Trust-model maintainers | Core | SECURITY.md contact |

Exact GitHub handles remain those listed in `.github/CODEOWNERS`.

## Funding workstreams (proposed)

| Workstream | Cadence | Cost drivers | Funding status |
| --- | --- | --- | --- |
| CI compute (Lean + Python gates) | continuous | runners, cache | **Not secured** — project uses public Actions today |
| Capability / checker review | per release | expert reviewer time | **Not secured** |
| Foundry semantic review (Q3+) | per corpus release | domain experts | **Not secured** |
| Security response retainer | as needed | triage + disclosure | **Not secured** |
| Frontier collaboration liaison | quarterly | meetings + tracking | **Not secured** |

## Operating budget sketch (engineering estimate only)

Orders of magnitude for planning discussions — not invoices or grants:

- Minimal open-source maintenance: CI + one rotating on-call maintainer (hours/week).
- Corpus release with Q3 review: additional domain-expert days per release.
- Paid security audit of LeanLink / adapters: discrete project, not continuous.

## Decision rights

- Semantic / claim-class changes: RFC + dual review (domain + trust).
- Capability `stable` promotion: GOVERNANCE.md gates; never docs-only.
- Foundry public release: Foundry maintainers + license/privacy checklist.
- Spending / grant acceptance: project governance leads (human process; external).

## Sustainability options (unranked)

1. Academic / institute hosting with funded maintainer time.
2. Industry sponsorship scoped to open replay + registry (no closed TCB capture).
3. Grant programs for formal-math infrastructure.
4. Volunteer rotation with narrow on-call scope if funding is delayed.

## Exit-criterion labeling

Delivery roadmap exit criterion *"maintenance funding and ownership are
established"* is **deferred / human-external** until:

- named owners acknowledge the map above in project governance channels; and
- at least one funding or hosting commitment is recorded outside this repo.

Engineering deliverable for Milestone 6: **this plan + ownership map + CODEOWNERS alignment**.
