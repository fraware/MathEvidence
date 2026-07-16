# §21.10 Workflow-win log

Template for **Project Spec §21 item 10**: at least one external Lean
contributor or project confirms a **real workflow win** using MathEvidence
(computational evidence entering Lean without expanding the TCB).

**Do not invent entries.** Empty templates below are intentional.

This log is distinct from Milestone 0 user confirmations
(`user-confirmation.md`), but one person may satisfy both if the entry
explicitly scopes both a problem confirmation and a concrete workflow win.

**Process:** follow `docs/validation/outreach-checklist.md` § “§21.10
workflow win”. Rubric for statement reviews (if any) remains
`docs/validation/expert-review-rubric.md`.

## What counts

A workflow win counts only if:

- the respondent is external (not a MathEvidence maintainer);
- they describe a concrete Lean workflow problem they hit (or still hit);
- they confirm MathEvidence (or a MathEvidence-shaped path) helped or would
  help that workflow in a specific way (replay, discovery, Agent, Studio, etc.);
- at least one bottleneck ID from `docs/validation/bottlenecks.md` is cited
  or described equivalently;
- consent for this log is recorded.

CI green builds, internal demos, and maintainer self-reports do **not** count.

## Entry template (copy for each win)

### Win 1

| Field | Value |
| --- | --- |
| Date | _YYYY-MM-DD_ |
| Name | _optional_ |
| Affiliation / Lean project | |
| Role (contributor / library author / educator / other) | |
| Workflow problem (1–3 sentences) | |
| How MathEvidence helped (or would help) | |
| Capability / path used (e.g. `algebra.rational_equality` offline replay) | |
| Most relevant bottlenecks (IDs from bottlenecks.md) | |
| Overlaps Milestone 0 user-confirmation entry? | yes (User N) / no |
| Consent to list publicly in this file | yes / no / anonymize |
| Evidence links (issue, Zulip, PR, anonymized note) | |

_Additional wins: copy the table above as Win 2, Win 3, …_

## Summary status

| Metric | Status |
| --- | --- |
| Workflow wins completed | 0 / ≥1 |
| §21.10 exit | **open** (template committed; outreach pending) |
| Owner | Outreach lead (human); tracked in `remaining-spec-matrix.md` R2 rows |

Filling this log is required before the capability JSON may move to
`"stable"` (see `stable-capability-checklist.md`). Engineering packaging does
not close this gate.
