# Federation agreements ledger

Records **real** maintainer agreements for live metadata emit/consume.
Engineering fixtures alone do **not** close Milestone 4 live exits.

**Fixture peer records (not live):** [`../../evidence/federation/agreements/`](../../evidence/federation/agreements/)
(`federationLevel: fixture`; validated by `scripts/validate_federation.py`).

**Status:** live agreements remain **OPEN** (fixture peers only). See
[`../STATUS.md`](../STATUS.md) and [`../../KNOWN_TRUST_GAPS.md`](../../KNOWN_TRUST_GAPS.md).  
**Upgrade checklist:** [`../../evidence/federation/examples/UPGRADE_PATH.md`](../../evidence/federation/examples/UPGRADE_PATH.md)  
**Outreach copy:** [`../validation/outreach-email-templates.md`](../validation/outreach-email-templates.md) Emails 6–8  
**Agreement form:** [`../validation/federation-agreement-template.md`](../validation/federation-agreement-template.md)

| project_id | role | status | contact | agreed_at | notes |
| --- | --- | --- | --- | --- | --- |
| lean-smt | emitter | **OPEN** | — | — | Fixture emit + fixture agreement JSON. Send Email 7; fill on consent. |
| cslib | consumer | **OPEN** | — | — | Fixture consume + fixture agreement JSON. Send Email 6; fill on consent. |

Status values: `OPEN` | `proposed` | `agreed` | `live_smoke`.

## How to record a real agreement (do not invent)

1. Maintainer replies with consent to emit and/or consume shared federation
   metadata (schema pin acknowledged).
2. Set `status` to `proposed` when outreach is acknowledged; `agreed` when
   scope + contact + date are confirmed in writing (issue/PR/email archive).
3. Fill `contact` (public handle or consented anonymize), `agreed_at` (ISO date),
   and `notes` (link to issue/PR + emit/consume/bidirectional scope).
4. Keep `ownership: federated` / `soundnessStatus: absent` on registry entries —
   never replace their checkers.
5. Only after **≥2** `agreed` (or `live_smoke`) rows, follow UPGRADE_PATH to
   opt-in live smoke. Do **not** claim `integrationMode=live` earlier.

Do not invent agreements. When a row moves to `agreed`, link the issue/PR and
enable optional `MATHEVIDENCE_FEDERATION_LIVE` smoke for that peer.
