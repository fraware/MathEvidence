# P4 blocker status — Live federation

**Purpose:** Maximize outreach + upgrade-path readiness so maintainers can
agree to live emit/consume. Fixtures alone do **not** close Milestone 4 live
exits.

**Do not invent** agreements, contacts, or `agreed_at` dates.  
**Do not** set `integrationMode=live` (or claim live peers) without ledger rows.

**Collaboration notes:** [`../architecture/collaboration-cslib-lean-auto-smt.md`](../architecture/collaboration-cslib-lean-auto-smt.md)  
**Agreements ledger:** [`../architecture/federation-agreements.md`](../architecture/federation-agreements.md)  
**Upgrade path:** [`../../evidence/federation/examples/UPGRADE_PATH.md`](../../evidence/federation/examples/UPGRADE_PATH.md)

Status vocabulary:

| Status | Meaning |
| --- | --- |
| `READY_FOR_HUMAN` | Outreach / checklist ready; a human must send / record |
| `BLOCKED_WAITING` | Waiting on maintainer reply or agreement |
| `ENGINEERING_READY` | Fixture harness green; no live peers required |

Last packaging pass: 2026-07-16 (engineering only; no agreements invented).

---

## Engineering (already ready)

| Item | Status | Path / command |
| --- | --- | --- |
| Federation schema | `ENGINEERING_READY` | `schemas/federation-metadata.schema.json` |
| Fixture examples (emit + consume) | `ENGINEERING_READY` | `evidence/federation/examples/` |
| Validate + harness | `ENGINEERING_READY` | `just federation-validate` |
| Current `integrationMode` | `fixture_only` | See UPGRADE_PATH — **do not flip without peers** |

---

## Human / external (still OPEN)

| Step | Status | Exact path(s) |
| --- | --- | --- |
| Outreach CSLib maintainer | `READY_FOR_HUMAN` | [`outreach-email-templates.md`](outreach-email-templates.md) Email 6 |
| Outreach lean-smt / SMT maintainer | `READY_FOR_HUMAN` | [`outreach-email-templates.md`](outreach-email-templates.md) Email 7 |
| Optional lean-auto note | `READY_FOR_HUMAN` | Email 8 (consume-only ask) |
| Record ≥2 agreements | `BLOCKED_WAITING` | [`federation-agreements.md`](../architecture/federation-agreements.md) — both rows **OPEN** |
| Schema pin + adapter + smoke | `BLOCKED_WAITING` | Follow UPGRADE_PATH checklist per peer |
| Live harness under env gate | `BLOCKED_WAITING` | `MATHEVIDENCE_FEDERATION_LIVE=1` only after agreements |

**Exit when:** ≥2 distinct external projects in the ledger at `agreed` (or
`live_smoke`) **and** harness can run live emit/consume (or documented hybrid)
without inventing peers.

---

## Human todo

```text
[ ] Send Email 6 to CSLib contact
[ ] Send Email 7 to lean-smt / SMT contact
[ ] (optional) Send Email 8 to lean-auto
[ ] On consent, fill federation-agreements.md rows (real contact + date)
[ ] Complete UPGRADE_PATH steps 2–6 per peer
[ ] Only then consider live smoke / hybrid documentation
[ ] — Do NOT invent agreements or set integrationMode=live without peers
```

---

## Confirmation (packaging integrity)

| Claim | Truth |
| --- | --- |
| Fake agreements added? | **No** — ledger rows remain OPEN |
| `integrationMode` flipped to live? | **No** — remains `fixture_only` |
| Live emit/consume claimed? | **No** |
