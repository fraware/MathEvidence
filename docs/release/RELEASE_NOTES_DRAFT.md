# Release notes draft — engineering-closure public preview

**Status:** draft for a public preview of branch `engineering-closure`  
**Not a stable release.** No capability is promoted to `"stable"`.

## Summary

MathEvidence is published as an **experimental** open computational-evidence
platform for Lean. This preview packages protocol, checkers, adapters, Agent
API v0.1.0, Studio surfaces, registry, Foundry samples, and offline evidence
under honest limitation docs
([`KNOWN_TRUST_GAPS.md`](../security/KNOWN_TRUST_GAPS.md),
[`STATUS.md`](../STATUS.md)).

## Highlights

- **Trust posture documented:** known limitations and open human gates are
  explicit; do not invent confirmations or dual-area approvals.
- **Agent API v0.1.0:** operation-level HTTP API; bundle open/inspect/replay
  accept opaque **`bundleId` only** (raw paths rejected).
- **Evidence Bundle v0.2:** full Evidence Bundle trees use `.cjson` layout;
  dual-read retained for older consumers during migration.
- **Capability ID:** formal rational calculus is
  `algebra.formal_rational_calculus` (not analytic `HasDerivAt`).
- **Forensic suite:** `tests/forensic/` guards core trust properties.

## Explicit non-claims

- No stable capability promotion.
- No live external federation agreements.
- No completed external user-confirmation / workflow-win / usability study
  counts invented for this draft.
- No attested immutable CI green on a release tag claimed in-tree.
- Dev receipt HMAC/Ed25519 material is **not** production PKI.

## Upgrade / migration notes for users

1. Prefer Agent `bundleId` flows; do not pass filesystem paths to public open /
   inspect / replay endpoints.
2. Prefer Evidence Bundle **v0.2** trees under `evidence/`.
3. Use registry ID `algebra.formal_rational_calculus`; treat legacy
   `symbolic_calculus` path names under `evidence/conformance/` as fixture
   directory names only.
4. Read [`docs/security/KNOWN_TRUST_GAPS.md`](../security/KNOWN_TRUST_GAPS.md)
   before relying on any experimental capability.

## Next (human / org)

- External confirmations and review packets
  (`docs/validation/user-confirmation.md`, `docs/validation/review-packets/`).
- Live federation agreements (`docs/architecture/federation-agreements.md`).
- Multi-area CODEOWNERS and enforceable dual review.
- Immutable CI green evidence on a candidate release commit, then governance PR
  for any `stable` flip per `docs/validation/stable-capability-checklist.md`.
