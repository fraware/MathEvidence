# MATH-AI cross-context full replication protocol

**Status:** FROZEN BEFORE FULL REPLICATION EXECUTION  
**Date:** 2026-09-30  
**Prospective design origin:** 2026-08-27  
**Feasibility evidence commit:** `d4938cea70fe4713b7da9eef8574447f5bb14901`  
**Pinned project:** `946d2f7b14840837a5b641150c9df9008c4be9eb`  
**Lean:** 4.14.0, commit `410fab728470`

The final feasibility audit records all three fixed contexts as feasible and
all 12 singleton signatures as exact matches to the transferred primary
signatures. This document authorizes the second gate without changing any
context, mechanism, target, classifier rule, or precedence relation.

## Frozen contexts

- CX1R — RationalEquality
- RX2 — Counterexample
- RX3 — Level

Their exact imports, targets, alternative targets, proof bodies, and namespaces
are those sealed in the final feasibility evidence at commit
`d4938cea70fe4713b7da9eef8574447f5bb14901`.

## Frozen mechanisms

The full replication uses the four active mechanisms only, exactly as specified
in the 2026-08-27 prospective design:

1. SOURCE_CORRUPTION
2. INVALID_PROOF
3. PROHIBITED_PLACEHOLDER
4. WRONG_TARGET

UNKNOWN_TYPE remains excluded from this extension because its activity is
configuration-dependent in the primary experiment.

## State and intervention denominators

For each context, all `2^4 = 16` mechanism subsets are executed once as fresh
native candidates, yielding 48 state executions.

For every nonempty state, each present mechanism is removed independently and
the successor candidate is executed afresh. Each mechanism appears in
`2^3 = 8` states, giving `4 * 8 = 32` directed removal edges per context and
96 intervention executions total.

No result from the accepted 32-state/80-edge primary experiment is pooled into
these denominators.

## Transferred prediction

The prediction is fixed from the accepted primary study and is not relearned
from the new contexts:

`FRONTEND_REJECT < ENVIRONMENT_OR_ELAB_REJECT < TOOLCHAIN_ACCEPT_POLICY_REJECT < TOOLCHAIN_ACCEPT_TARGET_MISMATCH < TOOLCHAIN_ACCEPT_TARGET_MATCH`.

The mechanism signatures are fixed as:

- SOURCE_CORRUPTION -> FRONTEND_REJECT
- INVALID_PROOF -> ENVIRONMENT_OR_ELAB_REJECT
- PROHIBITED_PLACEHOLDER -> TOOLCHAIN_ACCEPT_POLICY_REJECT
- WRONG_TARGET -> TOOLCHAIN_ACCEPT_TARGET_MISMATCH

For each state, the transferred model predicts the earliest present signature
under this ordering, or target match for the clean state.

For intervention edges, removing the currently exposed mechanism predicts a
class change. Removing a later masked mechanism predicts class preservation.
With four active mechanisms, each context contains 15 exposed-removal edges
and 17 masked-active-removal edges.

## Analysis and retention rules

- Every execution and every `UNKNOWN` is retained.
- Construction metadata is excluded from classification.
- The already-frozen hardened v2 classifier is reused unchanged.
- Results are reported per context before any aggregate count.
- The transferred prediction is the primary analysis. A context-local model
  may only be reported as secondary descriptive analysis.
- Counterexamples receive the same reporting priority as matches.
- Full-replication evidence is ineligible for publication until an independent
  recomputation checks all 48 state predictions and all 96 edge predictions.
- The failed first feasibility smoke and the IdealMembership build failure
  remain preserved in branch history and are not rewritten by this run.
