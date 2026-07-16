# Federation agreements ledger

Records **real** maintainer agreements for live metadata emit/consume.
Engineering fixtures alone do **not** close Milestone 4 live exits.

**Readiness board:** [`../validation/p4-blocker-status.md`](../validation/p4-blocker-status.md)  
**Upgrade checklist:** [`../../evidence/federation/examples/UPGRADE_PATH.md`](../../evidence/federation/examples/UPGRADE_PATH.md)  
**Outreach copy:** [`../validation/outreach-email-templates.md`](../validation/outreach-email-templates.md) Emails 6–8

| project_id | role | status | contact | agreed_at | notes |
| --- | --- | --- | --- | --- | --- |
| lean-smt | emitter | **OPEN** | — | — | Fixture emit only (`evidence/federation/examples/lean_smt_emit.json`). Send Email 7; fill on consent. |
| cslib | consumer | **OPEN** | — | — | Fixture consume only (`evidence/federation/examples/cslib_consume.json`). Send Email 6; fill on consent. |

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
