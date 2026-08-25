# ADR 0005 — Exact candidate binding is required for theorem certification

## Status

Accepted.

## Decision

A theorem-level Certification Record may be issued only when the exact submitted
candidate was verified by the declared trusted path.

Consequences:

1. A theorem about a fixture, protocol self-test, or nearby proposition cannot
   certify a different submitted candidate.
2. Exact assurance requests never silently downgrade to fixture or bridge replay.
3. Float values never coerce into exact rational/integer certificates.
4. Generated Lean for exact replay is produced from a validated typed
   representation of the candidate (request + certificate), not from untrusted
   raw caller Lean fragments.
5. Checker existence, offlineFixtures, benchmark scores, and numerical agreement
   never authorize Certification Record promotion by themselves.

## Context

Generic kernel replay previously selected broad `OfflineFixtures` by
capability/profile while constructing candidate-specific Certification Record
metadata. That allowed a valid fixture theorem to be recorded against a different
submitted claim. The exact-candidate-binding workstream ([PR #53](https://github.com/fraware/MathEvidence/pull/53)
and follow-on) repairs that class of failure.

The live source of truth for what each capability may prove, and whether a
result may mint a Certification Record, is
[`registry/maturity-inventory.json`](../../registry/maturity-inventory.json).
Operator runbook: [`docs/HANDOFF.md`](../HANDOFF.md).
Historical `MET` labels in dated audits and older status snapshots remain
historical engineering-artifact records. They are not current theorem-level
authority.

## Policy

Owned exact-bound capabilities may set `cr_eligible=true` only after generator,
declaration-identity, offline regenerability, and tamper gates — never from
checker-only changes. Live `cr_eligible` / `allowedOutcomes` live in
[`registry/maturity-inventory.json`](../../registry/maturity-inventory.json) and
each capability's `assurancePolicy`. Federated SAT / PB / SMT remain metadata
only and are never CR-eligible under exact binding.

At ADR acceptance on the baseline pin, catalog capabilities started with
`cr_eligible=false`. Do not read that historical snapshot as current status —
consult the maturity inventory.

## Revisit condition

Revisit a capability's `cr_eligible` bit only after that capability has an exact
generator, declaration-identity verification, offline replay, and tamper tests,
and only via the assurance-policy registry. A checker-only change must not flip
`cr_eligible`.
