# ADR 0001 — Use a single monorepo with hard trust boundaries

## Decision

All MathEvidence products live in one repository. Dependency direction and CODEOWNERS enforce separation between Lean theorem code, adapters, agents, studio, foundry, and benchmarks.

## Rationale

The protocol, checkers, adapters, conformance suites, and datasets must evolve together during the foundational phase. Separate repositories would create version skew and weaken end-to-end testing. The monorepo does not permit architectural coupling; import-boundary CI enforces the trust model.
