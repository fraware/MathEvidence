# MathEvidence

**Open computational evidence infrastructure for Lean.**

MathEvidence lets Lean users, mathematical AI agents, and research tools delegate expensive mathematical search or computation to external systems while keeping Lean as the sole authority for theorem acceptance.

The repository is a monorepo containing a solver-independent protocol, typed semantic encodings, verified evidence checkers, backend adapters, AI-facing APIs, notebook and editor integrations, a capability registry, a training-data foundry, benchmarks, and the documentation needed to govern the complete system.

## Problem

Formal mathematical developments repeatedly need capabilities that mature external systems already provide, including exact algebra, optimization, finite search, symbolic calculus, recurrence solving, and scientific computation. Existing integrations are usually bespoke. Each reinvents expression translation, side-condition handling, trust boundaries, evidence formats, solver invocation, failure reporting, and replay.

This fragmentation creates four costs.

1. External results are difficult to admit without expanding the trusted computing base.
2. Semantic mistakes at the translation boundary can produce formally checked statements that do not match the intended mathematics.
3. Integrations cannot be reused across backends, domains, formalization projects, or AI agents.
4. Tool-use trajectories are not captured as structured data for future mathematical systems.

## North Star

> Every external computation that contributes to a formal mathematical conclusion crosses into Lean through an explicit semantic contract and independently checkable evidence, producing a reusable theorem without trusting the external solver.

## Non-negotiable invariants

- External backends are untrusted.
- The original Lean proposition is authoritative.
- Types, assumptions, domains, branches, and claim strength are explicit.
- A backend Boolean answer is never sufficient evidence.
- Every accepted result is bound to the exact request by a cryptographic digest.
- Rechecking committed evidence requires only open Lean code and stored artifacts.
- Mathlib-facing packages never depend on Mathematica, SageMath, SymPy, Python, notebooks, or network services.
- Witness validity, soundness, completeness, optimality, and approximation are distinct claim classes.
- Release artifacts contain no `sorry`, project-specific axioms, or hidden solver dependencies.
- Existing domain projects remain authoritative; MathEvidence integrates them instead of replacing them.

## Repository map

- `MathEvidence/` — Lean semantics, protocol types, verified encodings, checkers, tactics, registry interfaces, and test infrastructure.
- `adapters/` — untrusted solver adapters. Mathematica evidence is produced via `wolframscript` on licensed hosts or committed as offline fixtures; LeanLink remains a scaffold until the review in `docs/architecture/leanlink-adapter-review.md` closes. SageMath and SymPy provide open reference backends.
- `agent/` — AI-facing operation API and SDKs.
- `studio/` — Mathematica notebook and editor experiences.
- `foundry/` — schemas and pipelines for certified tool-use episodes.
- `registry/` — machine-readable capability and backend declarations (capabilities stay `experimental` until governance gates pass).
- `benchmarks/` — real-world, adversarial, and conformance suites.
- `evidence/` — small committed evidence bundles used for examples and offline replay.
- `docs/` — master specification, standalone product specifications, RFCs, architecture decisions, and threat models.

## First implementation wedge

Version 0 proves the architecture through three end-to-end capabilities.

1. Rational-function equality with explicit denominator conditions.
2. Exact linear algebra, beginning with matrix inverses and linear-system witnesses.
3. Finite counterexamples for false formal conjectures.

**Current dual-backend evidence:** `algebra.rational_equality` has SymPy live
generation plus Mathematica live generation via `wolframscript` when
`MATHEVIDENCE_WOLFRAMSCRIPT` is set (public CI without Wolfram uses committed
offline fixtures and differential `skip`/`fixture`). `analysis.symbolic_calculus`
likewise has SymPy live plus Mathematica live derivative/antiderivative via the
same wolframscript gate (candidate ≠ completeness; CI offline fixtures when
Wolfram is absent). Linear algebra and finite counterexample have SymPy
`conformance_verified` plus Mathematica/Sage `live_generator_complete` generators
(CI fixture when Wolfram/Sage absent); see `registry/` and
`docs/validation/remaining-spec-matrix.md`.

The architectural target is that each capability support Mathematica and at least one open backend while using one shared Lean checker per claim type.

## Delivery rule

The project does not generalize the protocol in anticipation of future domains. New abstractions are admitted only after two independent domain implementations demonstrate the common requirement.

See `docs/PROJECT_SPEC.md` for the normative project specification and `docs/REPOSITORY_ARCHITECTURE.md` for the complete monorepo design. Honest status against §21 and milestone exits: `docs/validation/remaining-spec-matrix.md`.
