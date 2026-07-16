# Product 2 — Certified Computation Service

## 1. Purpose

The Certified Computation Service orchestrates a complete computational proof action from a Lean goal to a reusable theorem. It recognizes supported operations, invokes an untrusted backend, validates returned evidence, produces the strongest justified claim, and emits an offline-replayable bundle.

## 2. Exact problem solved

Domain integrations currently combine recognition, translation, process management, solver calls, output parsing, checking, theorem construction, and user reporting in one tactic. This makes them difficult to reuse across backends and agents.

The service standardizes the lifecycle while leaving domain mathematics in independent checker packages.

## 3. Responsibilities

- capability recognition;
- request construction;
- backend selection;
- resource policy;
- invocation and cancellation;
- evidence normalization;
- checker dispatch;
- theorem and side-goal production;
- provenance capture;
- evidence bundle creation;
- replay;
- and structured diagnostics.

## 4. Non-responsibilities

- defining domain truth;
- trusting backend status;
- implementing every solver algorithm;
- proving checker soundness;
- or hiding unresolved assumptions.

## 5. Backend protocol

JSON-RPC over stdio is mandatory for v0.

Methods:

- `initialize`
- `listCapabilities`
- `checkSupport`
- `compute`
- `cancel`
- `shutdown`

The service starts a fresh process by default. Daemon mode is experimental until performance data justifies its security and lifecycle complexity.

## 6. Selection policy

Backend selection considers:

- requested claim strength;
- supported fragment;
- open versus proprietary preference;
- deterministic mode;
- expected cost;
- certificate size;
- user policy;
- and local availability.

The default policy prefers an open backend when expected capability is equivalent. Mathematica may be preferred for operations where it has materially stronger generation capability.

## 7. Evidence handling

Backend output enters one of four categories:

1. Candidate only.
2. Candidate plus witness.
3. Candidate plus certificate.
4. Search hint or trace.

Only categories 2 and 3 can directly establish a theorem. Category 1 may be internally verified by a checker that requires no additional certificate. Category 4 feeds Trace-to-Plan and never changes theorem status by itself.

## 8. Replay

Replay is a separate command and code path. It does not discover or start backends. It loads a bundle, validates hashes and versions, runs the designated checker, and recreates the theorem or report.

A bundle whose checker version is unsupported produces a migration-required status, never silent reinterpretation.

## 9. Lean UX

`mathevidence` displays a concise report:

```text
Operation: rational equality over ℚ
Backend: Mathematica 15.x via LeanLink
Requested: sound result
Established: soundness verified
Added conditions: x ≠ 0
Assurance: verified reflection
Evidence: .mathevidence/bundles/<digest>
Remaining goals: 1
```

Detailed diagnostics are available on demand.

## 10. Agent UX

The API returns typed fields and stable error codes. Agents can request a capability explicitly or ask for recognition. The service records whether the agent requested a stronger claim than the backend/checker could establish.

## 11. Security

- fixed executable allow-list;
- no shell invocation;
- process isolation;
- resource limits;
- output limits;
- strict schema validation;
- cancellation propagation;
- and no credentials in bundles.

## 12. Failure modes

- operation misclassification;
- adapter returns a weaker claim;
- evidence valid for a different request;
- backend timeout;
- checker performance regression;
- and replay schema drift.

Each has a distinct error code and test.

## 13. Acceptance criteria

1. One Lean tactic works with Mathematica and an open backend.
2. The same checker decides both results.
3. Offline replay passes with all adapters disabled.
4. A malformed or mismatched response cannot create a theorem.
5. Timeouts and cancellation leave no orphan process.
6. Users and agents receive exact claim status and unresolved conditions.
7. The service adds no domain axiom or backend trust.
