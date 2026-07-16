# Studio usability — facilitator card (one sitting)

**Human results stay OPEN until real participants complete sessions.**  
Do not invent labels, pass rates, or quotes.  
**Board:** [`../../p1-blocker-status.md`](../../p1-blocker-status.md) · **Protocol:** [`PROTOCOL.md`](PROTOCOL.md)

## Before the first participant (5 min)

- [ ] Surface ready: VS Code extension **or** Wolfram Studio notebook
- [ ] Golden / Computed / Ambiguous / Certified payloads available
      (`studio/golden/transcripts/` for expected machine behavior)
- [ ] Consent language ready (public defect notes vs anonymize)
- [ ] Open `defect-log.md` and the three session templates S01–S03
- [ ] Invite sent (Email 4 in `outreach-email-templates.md`) or walk-up consented

## Per session (~20 min)

| Min | Action |
| --- | --- |
| 0–5 | Brief: Studio is not a checker; Certified requires Lean status |
| 5–15 | Run scripted steps from S01 / S02 / S03 |
| 15–20 | Debrief: false confidence? missing assumptions? |
| after | Fill result rows; file defects; leave OPEN cells only if incomplete |

## Pass key (do not show participant)

| Session | Critical check |
| --- | --- |
| S01 | Ambiguous when Lean status missing; Certified only with Lean + proposition |
| S02 | Certify workflow refuses Certified without Lean |
| S03 | Assumptions visible before Certified affordance |

## After ≥3 completed sessions

- [ ] All three session outcome fields filled (pass/fail + notes)
- [ ] Defects triaged in `defect-log.md`
- [ ] Update Product 09 acceptance only when humans finished — do not flip
      capability `stable` from Studio alone
- [ ] Mark corresponding rows on [`p1-blocker-status.md`](../../p1-blocker-status.md)

## If blocked

Record blocker in `defect-log.md` (environment, consent refusal, no participants)
and leave session outcomes **OPEN**. Do not invent fill-ins to clear the board.
