# ME-RV-086 — External adoption integration checklist

One external project must consume a released MathEvidence package, use a
capability in its own repository, and replay evidence without a backend.

**Status: BLOCKED(human)** — 0 external adoptions.
Do not invent PRs, package pins, or maintainer contacts. In-tree demos and
copied examples are **not** adoption.

**GitHub:** https://github.com/fraware/MathEvidence/issues/48  
**Issue form:** `.github/ISSUE_TEMPLATE/external_adoption.yml`  
**Log twin:** `docs/validation/adoption-log.md`  
Normative: `docs/audits/2026-07-26-real-vision/12_REGISTRY_GOVERNANCE_ADOPTION.md`.

## What counts

Adoption counts only if all of the following are true:

- adopting project is external (not MathEvidence itself);
- consumes a **released** MathEvidence package (tag / release asset / published dep);
- uses a named capability in the external repository (commit/PR evidence);
- replays evidence offline without trusting a backend as authority;
- integration feedback recorded;
- maintainer contact identified with consent.

## Integration checklist (fill when real)

| Field | Value |
| --- | --- |
| Date | _YYYY-MM-DD_ |
| External project name | |
| Project URL / repo | |
| Maintainer contact | |
| Released package consumed (tag / version / URL) | |
| Capability used | |
| External PR / commit using the capability | |
| Offline replay path (command or doc link) | |
| Backend used for discovery only? (yes/no/n/a) | |
| Integration feedback (summary or link) | |
| Overlaps §21.10 workflow-win entry? | yes (Win N) / no |
| Consent to list publicly | yes / no / anonymize |
| Notes | |

## Acceptance boxes (leave unchecked until true)

- [ ] Consumes released MathEvidence package
- [ ] Uses capability in external repository (link PR/commit)
- [ ] Replays evidence without backend authority
- [ ] Integration feedback recorded
- [ ] Maintainer contact identified
- [ ] Not a copied in-tree example presented as adoption
- [ ] Entry mirrored in `adoption-log.md` when consented
- [ ] Issue #48 updated with real links only

## Summary

| Metric | Status |
| --- | --- |
| External adoptions completed | **0 / ≥1** |
| ME-RV-086 | **BLOCKED(human)** |
