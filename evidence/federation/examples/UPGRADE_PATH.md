# Federation upgrade path (fixture_only → live)

Honesty rule: examples under `evidence/federation/examples/` are **fixtures**.
Do not claim live external emit/consume, maintainer sign-off, or process
integration until the checklist below is complete for each peer.

## Current mode

| Field | Value |
| --- | --- |
| `integrationMode` | `fixture_only` |
| Live env gate | `MATHEVIDENCE_FEDERATION_LIVE=1` (opt-in; still requires agreements) |
| Agreements ledger | `docs/architecture/federation-agreements.md` |

## Upgrade checklist (per external project)

1. **Maintainer agreement** — recorded in `federation-agreements.md` with
   contact, date, and scope (emit / consume / bidirectional). Do not invent.
2. **Schema pin** — peer confirms `federationVersion` and claim/status enums.
3. **Emit or consume adapter** — thin metadata wrapper only; no checker fork.
4. **Round-trip smoke** — harness pairs emit digest with consume digest under
   env gate; offline fixtures remain green without the peer.
5. **Registry honesty** — federated capability `supportLevel` stays metadata
   until dual review; never upgrade checker ownership.
6. **CI policy** — public CI stays offline-fixture; live smoke is optional
   self-hosted / maintainer CI.

## Harness commands

```text
# Always (fixture_only contract)
python scripts/validate_federation.py
python scripts/run_federation_harness.py

# Opt-in live smoke (fails closed if agreements missing)
set MATHEVIDENCE_FEDERATION_LIVE=1
python scripts/run_federation_harness.py --live-check
```

## Exit criterion mapping

Milestone 4 “≥2 existing projects consume or emit shared metadata” stays
**OPEN** for live peers. Fixture harness coverage is engineering-only and does
not close the research/external exit.
