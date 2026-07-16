# Human gates — one-sitting runbook

Engineering on `implement/master-plan` is packaged. This page is the **only**
checklist a human needs to close every remaining OPEN governance / outreach /
usability row without inventing artifacts.

**Do not** set `"status": "stable"` or invent users, signatures, funding, or
session results.

**Time budget (realistic):** ~3–4 hours if contacts respond the same day; else
spread across outreach follow-ups.

## Prep (15 min)

1. Run `just check` (or confirm latest green CI on `implement/master-plan`).
2. Skim trust one-pager: `docs/SECURITY_AND_TRUST_MODEL.md`.
3. Have demo ready: `just replay` + optional SymPy discovery
   (`MATHEVIDENCE_DISCOVERY=1`).
4. Open this folder: `docs/validation/`.

## Track A — Outreach (Milestone 0 + §21.10 + adoption) (~60–90 min active)

| Step | Action | Fill |
| --- | --- | --- |
| A1 | Pick ≥3 external candidates (Zulip / educators / library authors) | `outreach-checklist.md` |
| A2 | Send email #1 (problem confirmation) from templates below | copy/paste |
| A3 | Send email #2 (workflow win) to at least one Lean contributor | copy/paste |
| A4 | On consent, file ≥3 rows | `user-confirmation.md` |
| A5 | On consent, file ≥1 workflow win | `workflow-win-log.md` |
| A6 | Optional: adoption ask → | `adoption-log.md` |

Templates: [`outreach-email-templates.md`](outreach-email-templates.md).

## Track B — Domain expert packet (~45–60 min reviewer time)

| Step | Action | Fill |
| --- | --- | --- |
| B1 | Convert `review-packets/SAMPLE-rational-equality-unsigned.md` using `TEMPLATE.md` | signed packet (new file, drop `-unsigned`) |
| B2 | Score with `expert-review-rubric.md` (pass bar) | same packet |
| B3 | Optional Hypothesis interfaces A/B/C | `HYPOTHESIS-IFACE-*-unsigned.md` |

## Track C — Studio usability (≥3 sessions, ~20 min each)

| Step | Action | Fill |
| --- | --- | --- |
| C1 | Read `studio/usability/PROTOCOL.md` + facilitator card | — |
| C2 | Run S01, S02, S03 with non-author participants | session result rows |
| C3 | File defects | `studio/usability/defect-log.md` |

Facilitator card: [`studio/usability/FACILITATOR_CARD.md`](studio/usability/FACILITATOR_CARD.md).

## Track D — Stable promotion PR (only after A+B)

| Step | Action | Artifact |
| --- | --- | --- |
| D1 | Confirm every box in `stable-capability-checklist.md` | links to logs/packets/CI |
| D2 | Open PR with body from `stable-promotion-draft.md` | registry status only |
| D3 | Two-area approvals per `GOVERNANCE.md` | PR approvals |

## Still intentionally human / external (not this sitting alone)

| Row | Why |
| --- | --- |
| Live federation ≥2 peers | Maintainer agreements — `federation-agreements.md` |
| Funding / frontier acceleration | Org / research — `docs/foundry/exit-gate-status.md` |
| Trained Foundry selector uplift | Research train/eval — not packaging |

## Exit when done

- `user-confirmation.md` ≥3 completed
- `workflow-win-log.md` ≥1 completed
- ≥1 signed domain review packet (not SAMPLE-unsigned)
- Studio S01–S03 result rows filled (or defects + deferred note)
- Then — and only then — promotion PR using `stable-promotion-draft.md`
