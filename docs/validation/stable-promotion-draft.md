# Draft: stable promotion note for `algebra.rational_equality`

**Status of this document:** draft packaging only.  
**Capability JSON today:** `"status": "experimental"`.  
**This file does not change the registry.** Do not merge a `stable` flip until
every human box in `stable-capability-checklist.md` has real artifacts.

**G3 status:** `BLOCKED_WAITING` on G1 — see [`g3-blocker-status.md`](g3-blocker-status.md).
G2 (wolframscript ADR) is engineering-complete; it does **not** authorize the
JSON flip without G1.

## Engineering packaging (ready)

Engineering prerequisites on the checklist are ticked with CI / `just check`
evidence (see that file). Reviewers can re-verify with:

```text
just check
```

Required public workflows: `lean.yml`, `adapter-conformance.yml`,
`offline-replay.yml`, `adversarial.yml` (see `.github/workflows/README.md`).

## Remaining human gates (still OPEN)

| Gate | Owner | Artifact when closed | Current |
| --- | --- | --- | --- |
| Domain expert review (signed packet) | Domain / Semantic IR | Completed packet under `docs/validation/review-packets/` (not SAMPLE-unsigned) | OPEN — sample unsigned only |
| Trust-model review (second area) | Core and trust model (+ different-area approver) | `review-packets/trust-model-YYYY-MM-DD.md` from `TRUST-MODEL-TEMPLATE.md`, or PR note + checklist | OPEN |
| Milestone 0: ≥3 external user confirmations | Outreach lead | `docs/validation/user-confirmation.md` (≥3 completed) | OPEN — 0/3 |
| §21.10 workflow win | Outreach lead | `docs/validation/workflow-win-log.md` (≥1 completed) | OPEN — 0 entries |
| Capability JSON PR + two-area approvals | Registry + Core/trust; domain co-review | PR changing status; `GOVERNANCE.md` two-area approvals | OPEN — not opened |

Outreach process: `docs/validation/outreach-checklist.md`.  
Expert rubric: `docs/validation/expert-review-rubric.md`.  
G1 readiness board: `docs/validation/g1-blocker-status.md`.

## Exact JSON change for a later PR (do not apply now)

File: `registry/capabilities/algebra.rational_equality.json`

### 1. Status field

```diff
-  "status": "experimental",
+  "status": "stable",
```

### 2. `knownLimitations` (replace the experimental governance bullet)

Current limitation text includes:

> Status remains experimental until docs/validation/stable-capability-checklist.md gates pass (governance; not docs-only).

After a real promotion, replace that bullet with something like:

> Promoted to stable under docs/validation/stable-capability-checklist.md (link PR + CI run URLs + review packet paths in the PR description). Equality remains only under explicit nonzero denominator conditions; no identity-at-poles claim.

Do **not** invent PR URLs, reviewer names, or confirmation counts in the JSON
until those artifacts exist.

### 3. Ready-to-paste promotion PR body (fill links after gates)

```markdown
## Summary

- Promote `algebra.rational_equality` from `experimental` to `stable` after
  human governance gates on `docs/validation/stable-capability-checklist.md`.
- Diff limited to capability status (+ `knownLimitations` governance bullet).

## Human gates (must be real; do not invent)

| Gate | Artifact |
| --- | --- |
| Domain expert signed packet | `docs/validation/review-packets/<completed>.md` |
| Trust-model second-area review | this PR approval from Core/trust area |
| Milestone 0 ≥3 confirmations | `docs/validation/user-confirmation.md` (summary) |
| §21.10 workflow win ≥1 | `docs/validation/workflow-win-log.md` |
| Engineering | green `just check` + workflows lean / adapter-conformance / offline-replay / adversarial |

## Test plan

- [ ] `just check` green on this branch
- [ ] Registry validates (`just registry-validate`)
- [ ] No other capability flipped
- [ ] Two approvals from different maintainer areas (`GOVERNANCE.md`)
- [ ] Explicit statement: no fabricated users/signatures

## Non-goals

- Does not claim funding, federation liveness, or Foundry frontier acceleration.
```

### 4. What the promotion PR must include

1. Diff limited to capability status (+ limitation text); no unrelated churn.
2. Links: green CI for the four workflows above; completed review packet path;
   user-confirmation summary (≥3); workflow-win-log entry (≥1).
3. Two approvals from different maintainer areas (`GOVERNANCE.md`).
4. Explicit statement that no user confirmations or expert signatures were
   fabricated.

## Non-goals of this draft

- Does not set `"status": "stable"` in the registry.
- Does not claim Milestone 0 or §21.10 closed.
- Does not claim funding, Foundry acceleration, or external adoption beyond
  what the human logs eventually record.
