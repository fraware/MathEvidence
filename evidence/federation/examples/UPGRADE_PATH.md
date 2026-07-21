# Federation upgrade path (fixture_only → live)

Honesty rule: examples under `evidence/federation/examples/` are **fixtures**.
Do not claim live external emit/consume, maintainer sign-off, or process
integration until the checklist below is complete for each peer.

**Agreements ledger:** `docs/architecture/federation-agreements.md`  
**Status:** live agreements remain OPEN — see `docs/STATUS.md` / `KNOWN_TRUST_GAPS.md`  
**Collaboration notes:** `docs/architecture/collaboration-cslib-lean-auto-smt.md`

## Current mode

| Field | Value |
| --- | --- |
| `integrationMode` | `fixture_only` |
| Live env gate | `MATHEVIDENCE_FEDERATION_LIVE=1` (opt-in; still requires agreements) |
| Agreements ledger | `docs/architecture/federation-agreements.md` (**0 agreed** until humans fill) |
| Peers needed for Milestone 4 live exit | ≥2 distinct external projects |

## Upgrade checklist (per external project)

Complete **in order**. Stop if any step lacks a real maintainer artifact.

1. **Maintainer agreement** — recorded in `federation-agreements.md` with
   contact, date, and scope (emit / consume / bidirectional). Do not invent.
   Outreach: Emails 6–8 in `docs/validation/outreach-email-templates.md`.
2. **Schema pin** — peer confirms `federationVersion` and claim/status enums
   against `schemas/federation-metadata.schema.json` (note version in ledger
   `notes` or linked issue).
3. **Emit or consume adapter** — thin metadata wrapper only; no checker fork.
   Keep `authority.checkerOwner = "external"` and
   `authority.mathEvidenceRole = "metadata_interop"`.
4. **Round-trip smoke** — harness pairs emit digest with consume digest under
   env gate; offline fixtures remain green without the peer.
5. **Registry honesty** — federated capability `supportLevel` stays metadata
   until dual review; never upgrade checker ownership;
   `soundnessStatus` stays `absent` unless their checker is in TCB (it is not).
6. **CI policy** — public CI stays offline-fixture; live smoke is optional
   self-hosted / maintainer CI.

## When (and only when) to document live / hybrid

| Condition | Allowed documentation |
| --- | --- |
| Ledger still all `OPEN` / `proposed` | Keep `integrationMode=fixture_only` |
| ≥1 `agreed` peer, fixtures still default | Document **hybrid**: fixtures in CI; named peer live-smoke opt-in |
| ≥2 `agreed` or `live_smoke` peers + smoke green | May document live emit/consume for those peers; keep ownership federated |

Never flip default CI to require live peers.

## Harness commands

```text
# Always (fixture_only contract)
python scripts/validate_federation.py
python scripts/run_federation_harness.py
# or: just federation-validate

# Opt-in live smoke (fails closed if agreements missing)
set MATHEVIDENCE_FEDERATION_LIVE=1
python scripts/run_federation_harness.py --live-check
```

## Exit criterion mapping

Milestone 4 “≥2 existing projects consume or emit shared metadata” stays
**OPEN** for live peers until the ledger has real rows. Fixture harness coverage
is engineering-only and does not close the research/external exit.
