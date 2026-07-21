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

This repository is an **experimental research platform** with reference
implementations. It is **not** a completed computational-evidence layer, and no
capability is stable. See [`KNOWN_TRUST_GAPS.md`](KNOWN_TRUST_GAPS.md).

Version 0 develops three capability tracks (honest status):

1. **Rational-function equality** — protocol / semantic-boundary **reference**
   (`role: protocol_reference`, `externalSearchEssential: false`). Lean can
   close many identities via `field_simp; ring` independently of backend output;
   this does **not** prove indispensable external computation.
2. **Exact linear algebra** — custom MatrixExpr IR witness checkers today;
   Mathlib `Matrix` goal reification remains open.
3. **Finite counterexamples** — custom FinitePredicate IR today; Mathlib goal
   reification remains open.

**Calculus:** `algebra.formal_rational_calculus` is **formal rational calculus**
only (planned rename to `algebra.formal_rational_calculus`). It does not
establish Mathlib `HasDerivAt` / analytic ODE theorems.

**Current dual-backend evidence:** `algebra.rational_equality` has SymPy live
generation plus Mathematica live generation via `wolframscript` when
`MATHEVIDENCE_WOLFRAMSCRIPT` is set (public CI without Wolfram uses committed
offline fixtures). Sage rational support is **declared/placeholder only**.
Linear algebra and finite counterexample have SymPy `conformance_verified`;
Mathematica/Sage generators may exist as adapters but Agent thin compute is
sympy-only until registry-driven dispatch lands — registry claims are
`implemented`, not overstated as live Agent routing. See `registry/` and
`docs/validation/remaining-spec-matrix.md`.

The architectural target is that each capability support Mathematica and at least one open backend while using one shared Lean checker per claim type.

**CI honesty:** workflow definitions exist under `.github/workflows/`; immutable
green runs on the audited baseline commit are not attested in-repo. Do not treat
local `just check` as promotion evidence.

## Delivery rule

The project does not generalize the protocol in anticipation of future domains. New abstractions are admitted only after two independent domain implementations demonstrate the common requirement.

See `docs/PROJECT_SPEC.md` for the normative project specification and `docs/REPOSITORY_ARCHITECTURE.md` for the complete monorepo design. Honest status against §21 and milestone exits: `docs/validation/remaining-spec-matrix.md`.
