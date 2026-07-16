# Product 7 — Capability Registry

## 1. Purpose

The Capability Registry is the authoritative machine-readable map of what MathEvidence can request, which backends can generate evidence, which Lean packages can check it, and what strength of theorem can be established.

## 2. Problem solved

Documentation pages routinely overstate or underspecify solver support. Humans and agents need exact, versioned capability claims with conformance evidence.

## 3. Capability record

Required fields:

- stable operation ID;
- semantic version;
- status: experimental, candidate, stable, deprecated;
- mathematical domain;
- input IR version;
- admissibility conditions;
- supported claim classes;
- evidence schema;
- checker module and version;
- assurance modes;
- resource limits;
- known limitations;
- conformance suite;
- and maintainers.

## 4. Backend record

Required fields:

- backend ID and version;
- adapter version;
- executable discovery method;
- license and availability constraints;
- supported capability versions;
- deterministic options;
- regeneration status;
- conformance result digest;
- and known defects.

## 5. Stability rules

A capability is `stable` only when:

- its semantics are normative;
- its checker has a soundness theorem;
- offline replay works;
- at least one backend passes conformance;
- limitations are documented;
- and compatibility policy is defined.

Two backends are required for flagship stable capabilities unless the domain has a justified single-provider constraint.

## 6. Query interfaces

- Lean API;
- command-line query;
- JSON export;
- Agent API capability discovery;
- Studio browsing.

Queries distinguish declared support, installed support, and conformance-verified support.

## 7. Failure modes

- stale backend claims;
- domain support presented too broadly;
- claim strength omitted;
- conformance results detached from versions;
- and registry becoming a marketing catalogue.

## 8. Acceptance criteria

1. Every stable capability is schema-valid and conformance-backed.
2. Agents can select tools without parsing prose.
3. Unsupported combinations are rejected before backend invocation.
4. Registry updates are versioned and reviewed by capability owners.
5. Historical bundle replay does not depend on mutable registry state.
