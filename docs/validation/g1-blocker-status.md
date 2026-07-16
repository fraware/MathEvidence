# G1 blocker status (engineering packaging)

**Purpose:** Maximize readiness so a human can finish G1-A through G1-D in one
sitting. This file tracks what engineering packaged vs what still needs a real
human.

**Do not invent** user confirmations, workflow wins, signed review packets,
trust signatures, or usability session results.  
**Do not** flip `registry/capabilities/algebra.rational_equality.json` to
`"status": "stable"`.

**Runbook:** [`human-gates-one-sitting.md`](human-gates-one-sitting.md)  
**Checklist:** [`stable-capability-checklist.md`](stable-capability-checklist.md)

Status vocabulary:

| Status | Meaning |
| --- | --- |
| `READY_FOR_HUMAN` | Templates, paths, and instructions exist; a human must fill them |
| `BLOCKED_WAITING` | Waiting on a prior human artifact or external response |
| `ENGINEERING_READY` | Re-confirm only; no new engineering work for G1 |

Last packaging pass: 2026-07-16 (engineering only; no human artifacts invented).

---

## G1-A — Outreach

| Step | Status | Exact path(s) to fill / use | Notes |
| --- | --- | --- | --- |
| A1 Select ≥3 contacts | `READY_FOR_HUMAN` | [`outreach-checklist.md`](outreach-checklist.md) — candidate source checkboxes | Leave unchecked until a real person is chosen |
| A2 Problem-confirmation emails | `READY_FOR_HUMAN` | [`outreach-email-templates.md`](outreach-email-templates.md) Email 1 | Copy/paste; replace bracketed fields |
| A3 Workflow-win ask | `READY_FOR_HUMAN` | [`outreach-email-templates.md`](outreach-email-templates.md) Email 2 | ≥1 Lean contributor |
| A4 ≥3 user confirmations | `BLOCKED_WAITING` | [`user-confirmation.md`](user-confirmation.md) — User 1 / 2 / 3 tables | **0/3 completed.** Fill only after consent. Do not invent people. |
| A5 ≥1 workflow win | `BLOCKED_WAITING` | [`workflow-win-log.md`](workflow-win-log.md) — Win 1 table | **0 entries.** Fill only after consent. Do not invent. |

**Exit when:** A4 ≥3/3 and A5 ≥1 with dated consent notes → then matrix S21.10 + M0.U.

---

## G1-B — Domain expert packet

| Step | Status | Exact path(s) to fill / use | Notes |
| --- | --- | --- | --- |
| B1 Create packet file | `READY_FOR_HUMAN` | Copy [`review-packets/SAMPLE-rational-equality-unsigned.md`](review-packets/SAMPLE-rational-equality-unsigned.md) → e.g. `review-packets/2026-rational-equality-<REVIEWER>.md` (**drop `-unsigned`**) | Or start from [`review-packets/TEMPLATE.md`](review-packets/TEMPLATE.md) |
| B2 Score rubric | `READY_FOR_HUMAN` | Same new packet + [`expert-review-rubric.md`](expert-review-rubric.md) | Pass bar: no zeros; ≥9/12; fidelity & claim strength ≥1 |
| B3 Sign | `BLOCKED_WAITING` | Same new packet — Reviewer + Decision sections | **0 signed packets.** SAMPLE remains unsigned on purpose. |

**Exit when:** ≥1 signed domain packet exists; tick Domain review on
[`stable-capability-checklist.md`](stable-capability-checklist.md).

Invite email: [`outreach-email-templates.md`](outreach-email-templates.md) Email 3.

---

## G1-C — Trust-model second-area review

| Step | Status | Exact path(s) to fill / use | Notes |
| --- | --- | --- | --- |
| C1 Second-area written review | `READY_FOR_HUMAN` | Copy [`review-packets/TRUST-MODEL-TEMPLATE.md`](review-packets/TRUST-MODEL-TEMPLATE.md) → `review-packets/trust-model-YYYY-MM-DD.md` **or** record the same content as a promotion-PR comment | Reviewer must be a different [`GOVERNANCE.md`](../../GOVERNANCE.md) area than the domain signer |
| C2 Checklist box | `BLOCKED_WAITING` | [`stable-capability-checklist.md`](stable-capability-checklist.md) — “Trust-model review” | Tick only after C1 exists |

**Exit when:** two distinct areas named on the record; checklist box `[x]`.

---

## G1-D — Engineering verification

| Step | Status | Exact path(s) / command | Notes |
| --- | --- | --- | --- |
| Local gate | `ENGINEERING_READY` | From repo root: `just check` | Recipe in `justfile` (`check:`). Re-confirm before promotion sitting. |
| CI workflows | `ENGINEERING_READY` | `.github/workflows/lean.yml`, `adapter-conformance.yml`, `offline-replay.yml`, `adversarial.yml` | Must be green on branch; index `.github/workflows/README.md` |
| Checklist eng boxes | `ENGINEERING_READY` | [`stable-capability-checklist.md`](stable-capability-checklist.md) Prerequisites section | Already `[x]` — do not re-litigate |

**Exit when:** human re-confirms green `just check` / CI on the sitting day. Does
**not** authorize `"status": "stable"`.

---

## Explicitly not G1 (do not fill as part of this sitting unless parallel)

| Item | Status | Path |
| --- | --- | --- |
| Studio S01–S03 session results | `BLOCKED_WAITING` (P1) | `docs/validation/studio/usability/sessions/` + [`p1-blocker-status.md`](p1-blocker-status.md) |
| Capability JSON → `stable` | `BLOCKED_WAITING` (G3) | **Blocked on G1.** See [`g3-blocker-status.md`](g3-blocker-status.md); draft [`stable-promotion-draft.md`](stable-promotion-draft.md) — do **not** open stable PR |
| Adoption log | Optional / Milestone 2 | [`adoption-log.md`](adoption-log.md) |
| Hypothesis A/B/C signed packets | Product P2 | [`p2-blocker-status.md`](p2-blocker-status.md) |
| Federation live agreements | Product P4 | [`p4-blocker-status.md`](p4-blocker-status.md) |

---

## Human todo list (copy into your sitting notes)

```text
[ ] A1  Pick ≥3 contacts          → outreach-checklist.md
[ ] A2  Send Email 1 ×3           → outreach-email-templates.md
[ ] A3  Send Email 2 ×≥1          → outreach-email-templates.md
[ ] A4  File ≥3 confirmations     → user-confirmation.md   (after consent)
[ ] A5  File ≥1 workflow win      → workflow-win-log.md    (after consent)
[ ] B1  Copy SAMPLE → signed file → review-packets/<name>.md
[ ] B2  Score rubric              → same file + expert-review-rubric.md
[ ] B3  Domain signature          → same file
[ ] C1  Trust-model note          → trust-model-YYYY-MM-DD.md or PR
[ ] C2  Tick trust checklist box  → stable-capability-checklist.md
[ ] D   Re-run / confirm          → just check + CI green
[ ] —   Do NOT flip stable yet
```

---

## Confirmation (packaging integrity)

| Claim | Truth |
| --- | --- |
| Fake users / confirmations added? | **No** — `user-confirmation.md` remains 0/3 |
| Fake workflow wins added? | **No** — `workflow-win-log.md` remains 0 entries |
| Signed domain packet invented? | **No** — only SAMPLE-unsigned + TEMPLATE |
| Trust signature invented? | **No** — only TRUST-MODEL-TEMPLATE |
| Capability flipped to stable? | **No** — remains `experimental` |
