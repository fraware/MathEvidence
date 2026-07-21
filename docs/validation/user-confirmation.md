# External User Confirmation Log (Milestone 0)

Template for recording ≥3 external users who confirm the problem MathEvidence
addresses (computational obligations entering Lean without expanding the TCB).

**Exit criterion:** at least three completed entries below with non-maintainer
affiliations.

**Related logs (do not confuse):**

| Need | File |
| --- | --- |
| Milestone 0 problem confirmations (≥3) | **this file** |
| §21.10 concrete workflow win (≥1) | `docs/validation/workflow-win-log.md` |
| Signed expert statement review | `docs/validation/review-packets/` |

**Outreach process:** `docs/validation/outreach-checklist.md` (do not invent
entries). Expert statement reviews use `docs/validation/expert-review-rubric.md`.
Status: see `docs/STATUS.md` / `docs/security/KNOWN_TRUST_GAPS.md` (0 confirmations until
real consent).

**Owner:** outreach lead (human). Engineering packaging does not close this
gate. Capability status remains **experimental**.

## Instructions

1. Share the project charter (`README.md` + trust model summary).
2. Ask whether they hit computational bottlenecks that match
   `docs/validation/bottlenecks.md`.
3. Record consent to list affiliation (or mark anonymous).
4. Do not collect private formalizations without explicit permission.
5. Prefer contacts who are not MathEvidence maintainers.
6. If the same contact also provides a §21.10 workflow win, file that win in
   `workflow-win-log.md` and cross-link the entry IDs.

## Validation quality bar (what counts)

A confirmation counts only if:

- the respondent is external (not a repo maintainer);
- they affirm the problem statement (computational→Lean trust gap);
- at least one bottleneck ID is cited or described equivalently;
- consent for this log is recorded.

Partial notes, internal demos, and CI green builds do **not** count.

## Confirmation entries

### User 1

| Field | Value |
| --- | --- |
| Date | _YYYY-MM-DD_ |
| Name | _optional_ |
| Affiliation | |
| Role (Lean user / library author / educator / other) | |
| Confirms problem statement? (yes/no) | |
| Most relevant bottlenecks (IDs from bottlenecks.md) | |
| Notes | |
| Cross-link to §21.10 workflow-win entry | none / Win N |
| Consent to list publicly in this file | yes / no / anonymize |

### User 2

| Field | Value |
| --- | --- |
| Date | _YYYY-MM-DD_ |
| Name | _optional_ |
| Affiliation | |
| Role (Lean user / library author / educator / other) | |
| Confirms problem statement? (yes/no) | |
| Most relevant bottlenecks (IDs from bottlenecks.md) | |
| Notes | |
| Cross-link to §21.10 workflow-win entry | none / Win N |
| Consent to list publicly in this file | yes / no / anonymize |

### User 3

| Field | Value |
| --- | --- |
| Date | _YYYY-MM-DD_ |
| Name | _optional_ |
| Affiliation | |
| Role (Lean user / library author / educator / other) | |
| Confirms problem statement? (yes/no) | |
| Most relevant bottlenecks (IDs from bottlenecks.md) | |
| Notes | |
| Cross-link to §21.10 workflow-win entry | none / Win N |
| Consent to list publicly in this file | yes / no / anonymize |

## Summary status

| Metric | Status |
| --- | --- |
| Confirmations completed | 0 / 3 |
| Milestone 0 user-confirmation exit | **open** (template + outreach checklist committed; outreach pending) |
| Capability JSON `stable` | **not applied** (see `stable-capability-checklist.md`) |

Outreach is intentionally outside the engineering skeleton. Filling this log is
required to close Milestone 0 product validation even after Phase 0 toolchain
gates pass.
