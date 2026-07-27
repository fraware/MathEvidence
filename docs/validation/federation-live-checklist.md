# ME-RV-082 / ME-RV-083 — Live federation agreement checklist

Fillable package for **live** federation peers. Fixture peers stay
`fixture_only` until every acceptance box below is true for that peer.

**Status: BLOCKED(human)** — 0 / 2 live peers.
Ledger: `docs/architecture/federation-agreements.md` (all rows OPEN).
Upgrade path: `evidence/federation/examples/UPGRADE_PATH.md`.
Agreement form: `docs/validation/federation-agreement-template.md`.

**GitHub:** [#44](https://github.com/fraware/MathEvidence/issues/44) (peer 1),
[#45](https://github.com/fraware/MathEvidence/issues/45) (peer 2)  
**Issue form:** `.github/ISSUE_TEMPLATE/federation_peer.yml`

Normative: `docs/audits/2026-07-26-real-vision/10_FOUNDRY_BENCHMARKS_AND_FEDERATION.md`.

## Honesty rules

- Do not flip `integrationMode` away from `fixture_only` until ≥2 peers are
  `agreed` or `live_smoke` with real maintainer artifacts.
- Fixture JSON under `evidence/federation/` does **not** close ME-RV-082/083.
- Public CI stays offline-fixture; live smoke is opt-in only.

## Per-peer checklist (copy for Peer 1 and Peer 2)

### Peer identity

| Field | Value |
| --- | --- |
| Peer slot | Peer 1 (ME-RV-082) / Peer 2 (ME-RV-083) |
| External project | |
| Project URL / repo | |
| Maintainer contact | |
| Role | emitter / consumer / bidirectional |
| Capability / schema accepted | |
| Schema / federation version pinned | |
| Digest algorithm agreed | |
| Status mapping documented | |
| Threat model documented (link) | |
| Revocation procedure documented (link) | |
| Signed / written agreement evidence | |
| Conformance suite green (CI or independent record) | |
| Ledger row updated (`proposed` → `agreed` → `live_smoke`) | no |
| Still `fixture_only`? | **yes** (default until signed) |
| Consent to list publicly | yes / no / anonymize |
| Notes | |

### Acceptance boxes (leave unchecked until true)

- [ ] Signed agreement recorded (issue / PR / email archive)
- [ ] Capability and version pinned
- [ ] Exact emitted / consumed roles documented
- [ ] Status mapping documented
- [ ] Digest algorithm agreed
- [ ] Threat model documented
- [ ] Maintainer contacts listed
- [ ] Conformance suite green (CI or independent record)
- [ ] Revocation procedure documented
- [ ] Not fixture_only metadata for this peer
- [ ] Ledger row in `federation-agreements.md` moved off OPEN with date + contact

### Peer 1 (ME-RV-082) — working copy

| Field | Value |
| --- | --- |
| External project | |
| Role | |
| Agreement evidence | |
| Checklist complete? | **no** |
| Status | **BLOCKED** — fixture_only |

### Peer 2 (ME-RV-083) — working copy

| Field | Value |
| --- | --- |
| External project | |
| Role | |
| Agreement evidence | |
| Checklist complete? | **no** |
| Status | **BLOCKED** — fixture_only |

## Summary

| Metric | Status |
| --- | --- |
| Live peers ready | **0 / 2** |
| ME-RV-082 | **BLOCKED(human)** |
| ME-RV-083 | **BLOCKED(human)** |
| Default integration mode | `fixture_only` |
