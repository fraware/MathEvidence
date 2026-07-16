# External Lean project adoption log (Milestone 2)

Template for **Delivery Roadmap Milestone 2**: one external Lean project adopts
a MathEvidence component (IR, checker, tactic, Agent API, Studio, or evidence
bundle workflow).

**Do not invent entries.** Empty templates below are intentional. Filling this
log is a **human/outreach** gate (same discipline as R2 user confirmations).

**Related:** §21.10 workflow wins live in `workflow-win-log.md`. An adoption
entry may overlap a workflow win if the same project both adopts a component
and confirms a concrete workflow improvement.

## What counts

An adoption entry counts only if:

- the adopting project is external (not MathEvidence itself);
- a named MathEvidence component is integrated or depended on (commit/PR/tag);
- the adoption is described in enough detail that a maintainer can reproduce
  the dependency or replay path;
- consent for this log is recorded.

Internal demos, CI green builds, and maintainer self-reports do **not** count.

## Entry template (copy for each adoption)

### Adoption 1

| Field | Value |
| --- | --- |
| Date | _YYYY-MM-DD_ |
| External project name | |
| Project URL / repo | |
| Contact (optional) | |
| Component adopted (e.g. `mathevidence` tactic, `algebra.linear_algebra` offline bundles, Agent API) | |
| How integrated (dependency / vendored IR / replay-only / Agent client) | |
| Evidence links (PR, commit, release note, Zulip) | |
| Overlaps §21.10 workflow-win entry? | yes (Win N) / no |
| Consent to list publicly in this file | yes / no / anonymize |
| Notes | |

_Additional adoptions: copy the table above as Adoption 2, …_

## Summary status

| Metric | Status |
| --- | --- |
| External adoptions completed | 0 / ≥1 |
| Milestone 2 adoption exit | **open** (template committed; outreach pending) |
| Owner | Outreach lead (human); tracked in `remaining-spec-matrix.md` |

Engineering R4 closes conformance, tactic ops, and Agent held-out measurement.
This log remains human-owned.
