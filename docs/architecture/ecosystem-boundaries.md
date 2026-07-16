# Ecosystem Boundaries

MathEvidence integrates external computation into Lean. It does **not** replace
specialized formal tools that already own their domains.

## What MathEvidence owns

- Solver-independent request / evidence / claim-status protocol.
- Restricted semantic IRs and reification soundness for supported domains.
- Verified Lean checkers and offline replay for those domains.
- Capability registry metadata and conformance reporting.
- Adapter boundaries that keep backends out of the theorem TCB.

## What MathEvidence does not replace

| Ecosystem | Boundary |
| --- | --- |
| **Mathlib** | Remains the mathematical library of record. MathEvidence produces theorems that compose with Mathlib; it is not a parallel library. |
| **CSLib / certified algorithms** | Authoritative for their verified algorithms. MathEvidence may consume or emit shared provenance metadata; it does not fork their checkers. |
| **Lean-SMT / SMT integrations** | Own SMT proof reconstruction and trusted interfaces. MathEvidence may federate capability metadata (Milestone 4) without subsuming solvers. |
| **Lean-auto / hammer tooling** | Automation search stays theirs. MathEvidence evidence is not a substitute for general proof search. |
| **Domain Gröbner / polynomial projects** | Remain authoritative for their certificates. Interop is metadata and optional adapters, not replacement. |
| **SAT / pseudo-Boolean checkers** | Same federation rule: shared status vocabulary, not a unified AST. |
| **Notebook / CAS UIs (Wolfram, etc.)** | Studio surfaces are clients of MathEvidence APIs. Certification still requires Lean replay. |

## Explicit non-goals

- A universal expression AST spanning all mathematics in v0.
- Trusting backend Booleans as theorems.
- Silently promoting witnesses to completeness or optimality claims.
- Requiring Mathematica for open-source replay CI.

## RFC posture

Cross-cutting protocol changes use `docs/rfcs/`. Domain semantics that stay
inside one capability may proceed under product specs without a new RFC, subject
to GOVERNANCE.md dual review for stable checkers.

See also `docs/adr/0002-solver-independence.md`, Milestone 4 in
`docs/DELIVERY_ROADMAP.md`, and collaboration notes in
`docs/architecture/collaboration-cslib-lean-auto-smt.md`.

Shared metadata schema: `schemas/federation-metadata.schema.json`.
Simulated emit/consume examples: `evidence/federation/examples/`.
