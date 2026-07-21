# External validation outreach checklist

Operational companion to:

- Milestone 0 confirmations: `docs/validation/user-confirmation.md`
- §21.10 workflow wins: `docs/validation/workflow-win-log.md`
- Expert statement reviews: `docs/validation/expert-review-rubric.md` +
  `docs/validation/review-packets/`

Completing outreach is **human work**. This checklist only makes the process
repeatable. Do **not** invent confirmations, signatures, or workflow wins.

**Status:** [`../STATUS.md`](../STATUS.md) · [`../security/KNOWN_TRUST_GAPS.md`](../security/KNOWN_TRUST_GAPS.md)  
**Copy/paste emails:** [`outreach-email-templates.md`](outreach-email-templates.md)  
**Stable promotion path:** [`stable-capability-checklist.md`](stable-capability-checklist.md)

## Before contacting anyone

- [ ] Bottleneck inventory reviewed (`docs/validation/bottlenecks.md`)
- [ ] Trust-model one-pager ready (`docs/security/SECURITY_AND_TRUST_MODEL.md`)
- [ ] Demo path ready: offline `mathevidence` replay + optional discovery with
      SymPy on a laptop (`MATHEVIDENCE_DISCOVERY=1`); or point reviewers at
      `just replay` / `MathEvidence.Tactic.Examples`
- [ ] Consent language prepared (public listing vs anonymize)
- [ ] Know which ask you need: problem confirmation (M0), workflow win
      (§21.10), signed statement review (domain gate), or all three
- [ ] Keep `user-confirmation.md` / `workflow-win-log.md` open — leave rows
      empty until real replies land

## Candidate sources (≥3 distinct non-maintainers)

Tick only when a **named** candidate is selected (not invented for the checklist):

- [ ] Mathlib / Lean Zulip domain experts (algebra / analysis as relevant)
      — contact: ________________
- [ ] Educators teaching Lean+CAS workflows
      — contact: ________________
- [ ] Library authors with computational proof obligations
      — contact: ________________
- [ ] Industry/research groups using Mathematica↔Lean bridges
      — contact: ________________

Spare slots if you need a fourth/fifth:

- [ ] Other: ________________

## Send log (optional sitting notes)

| Date | Contact | Email # (1 / 2 / 3) | Sent? | Reply? | Logged where |
| --- | --- | --- | --- | --- | --- |
| | | | | | |
| | | | | | |
| | | | | | |

## Per contact (Milestone 0 — problem confirmation)

1. Share README + trust boundary (adapters untrusted; Lean checker trusted).
2. Ask which bottlenecks match their work (IDs from `bottlenecks.md`).
3. Record yes/no on problem confirmation.
4. Obtain consent for `user-confirmation.md` listing.
5. File an entry **only after consent**; leave template rows empty otherwise.

## Per contact (§21.10 — workflow win)

1. Ask for a concrete Lean workflow problem (not a vibe check).
2. Record whether MathEvidence helped or would help that workflow specifically
   (replay / discovery / Agent / Studio — name the path).
3. Cite bottleneck ID(s); obtain consent.
4. File under `workflow-win-log.md`. If the same person also confirms the
   problem for Milestone 0, note the overlap in both logs explicitly.

## Per contact (domain expert packet — G1-B)

1. Use `review-packets/TEMPLATE.md` (or convert
   `SAMPLE-rational-equality-unsigned.md` — drop `-unsigned` in the new name).
2. Score with `expert-review-rubric.md`; pass bar must hold.
3. Real reviewer identity (or consented anonymize) — never placeholders.
4. Do not treat a signed packet as automatic `stable` promotion.
5. Invite: Email 3 in `outreach-email-templates.md`.

## Exit metrics

| Metric | Target | Log |
| --- | --- | --- |
| Confirmations in `user-confirmation.md` | ≥ 3 completed | Milestone 0 |
| Workflow wins in `workflow-win-log.md` | ≥ 1 completed | §21.10 |
| Maintainer-only entries | do **not** count | — |
| Signed domain review packet | ≥ 1 non-placeholder | `review-packets/` |

## Status (honest)

| Track | Status |
| --- | --- |
| Outreach execution | **pending** (human) |
| Milestone 0 confirmations | **0 / 3** — see `user-confirmation.md` |
| §21.10 workflow wins | **0 / ≥1** — see `workflow-win-log.md` |
| Signed domain packets | **0** — SAMPLE unsigned only |
| Trust-model second-area review | **0** — template only (`TRUST-MODEL-TEMPLATE.md`) |
| Capability `stable` | **not flipped** — engineering packaging only |

Owners and matrix rows: `docs/validation/remaining-spec-matrix.md`.
Promotion path (not applied): `docs/validation/stable-capability-checklist.md`.
