# P1 blocker status — Studio usability (Product 09)

**Purpose:** Maximize facilitation readiness for S01–S03 so a human can run
sessions and close Product 09 criterion 1. Engineering packages the protocol;
humans fill results.

**Do not invent** participant ids, labels, pass rates, quotes, or consent forms.  
**Do not** flip capability `stable` from Studio alone (that is G3 after G1).

**Protocol:** [`studio/usability/PROTOCOL.md`](studio/usability/PROTOCOL.md)  
**Facilitator card:** [`studio/usability/FACILITATOR_CARD.md`](studio/usability/FACILITATOR_CARD.md)  
**Product report:** [`products/09_studio.md`](products/09_studio.md)

Status vocabulary (same as G1 board):

| Status | Meaning |
| --- | --- |
| `READY_FOR_HUMAN` | Templates + instructions exist; a human must facilitate / fill |
| `BLOCKED_WAITING` | Waiting on participants, consent, or prior gate |
| `ENGINEERING_READY` | Machine / golden gates already green |

Last packaging pass: 2026-07-16 (engineering only; no session results invented).

---

## Facilitation materials

| Item | Status | Path |
| --- | --- | --- |
| Protocol (goals, flow, success bar) | `READY_FOR_HUMAN` | [`studio/usability/PROTOCOL.md`](studio/usability/PROTOCOL.md) |
| Facilitator card (one sitting) | `READY_FOR_HUMAN` | [`studio/usability/FACILITATOR_CARD.md`](studio/usability/FACILITATOR_CARD.md) |
| Session S01 — status identification | `READY_FOR_HUMAN` | [`studio/usability/sessions/S01_status_identification.md`](studio/usability/sessions/S01_status_identification.md) |
| Session S02 — certify workflow | `READY_FOR_HUMAN` | [`studio/usability/sessions/S02_certify_workflow.md`](studio/usability/sessions/S02_certify_workflow.md) |
| Session S03 — assumptions visibility | `READY_FOR_HUMAN` | [`studio/usability/sessions/S03_assumptions_visibility.md`](studio/usability/sessions/S03_assumptions_visibility.md) |
| Defect log | `READY_FOR_HUMAN` | [`studio/usability/defect-log.md`](studio/usability/defect-log.md) |
| Invite email | `READY_FOR_HUMAN` | [`outreach-email-templates.md`](outreach-email-templates.md) Email 4 |
| Golden / epistemic eng gates | `ENGINEERING_READY` | `studio/golden/`; `just studio-test` |

---

## Human session results (still OPEN)

| Session | Result rows | Status |
| --- | --- | --- |
| S01 | All OPEN | `BLOCKED_WAITING` — need real participant |
| S02 | All OPEN | `BLOCKED_WAITING` — need real participant |
| S03 | All OPEN | `BLOCKED_WAITING` — need real participant |
| Defects | Placeholder row only | `BLOCKED_WAITING` — file only from real sessions |

**Exit when:** ≥3 completed session outcome fields (pass/fail + notes) across
S01–S03 (or three distinct participants covering the critical checks), defects
triaged, Product 09 criterion 1 updated to PASS — without inventing data.

---

## Facilitator todo (copy into sitting notes)

```text
[ ] Surface ready (VS Code and/or Wolfram Studio)
[ ] Consent language ready
[ ] Open defect-log.md + S01–S03 templates
[ ] Brief: Studio is not a checker; Certified needs Lean
[ ] Run S01 / S02 / S03 (~20 min each)
[ ] Fill result rows; file defects
[ ] Update products/09_studio.md criterion 1 only after ≥3 real sessions
[ ] — Do NOT invent labels or flip capability stable
```

---

## Confirmation (packaging integrity)

| Claim | Truth |
| --- | --- |
| Fake session results added? | **No** — S01–S03 remain OPEN |
| Fake defects invented? | **No** — defect-log placeholder only |
| Product 09 criterion 1 flipped PASS? | **No** — remains OPEN (human) |
