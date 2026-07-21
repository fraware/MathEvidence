# MathEvidence

**Open computational evidence infrastructure for Lean.**

MathEvidence lets Lean users, mathematical AI agents, and research tools
delegate expensive mathematical search or computation to external systems while
keeping Lean as the sole authority for theorem acceptance.

The repository is a monorepo: solver-independent protocol, typed semantic
encodings, verified evidence checkers, backend adapters, an AI-facing Agent API,
notebook and editor integrations, a capability registry, a training-data
foundry, benchmarks, and governance docs.

**Public preview:** experimental research platform. No capability is stable.
See [`docs/STATUS.md`](docs/STATUS.md) and
[`docs/security/KNOWN_TRUST_GAPS.md`](docs/security/KNOWN_TRUST_GAPS.md).

## Problem

Formal developments repeatedly need capabilities mature external systems
already provide — exact algebra, optimization, finite search, symbolic
calculus, recurrence solving, scientific computation. Integrations are usually
bespoke: each reinvents expression translation, side conditions, trust
boundaries, evidence formats, solver invocation, failure reporting, and replay.

That fragmentation creates four costs:

1. External results are hard to admit without expanding the trusted computing base.
2. Semantic mistakes at the translation boundary can yield formally checked
   statements that do not match the intended mathematics.
3. Integrations do not reuse across backends, domains, projects, or agents.
4. Tool-use trajectories are not captured as structured data for future systems.

## North star

> Every external computation that contributes to a formal mathematical
> conclusion crosses into Lean through an explicit semantic contract and
> independently checkable evidence, producing a reusable theorem without
> trusting the external solver.

## Non-negotiable invariants

- External backends are untrusted.
- The original Lean proposition is authoritative.
- Types, assumptions, domains, branches, and claim strength are explicit.
- A backend Boolean answer is never sufficient evidence.
- Every accepted result is bound to the exact request by a cryptographic digest.
- Rechecking committed evidence requires only open Lean code and stored artifacts.
- Mathlib-facing packages never depend on Mathematica, SageMath, SymPy, Python,
  notebooks, or network services.
- Witness validity, soundness, completeness, optimality, and approximation are
  distinct claim classes.
- Release artifacts contain no `sorry`, project-specific axioms, or hidden
  solver dependencies.
- Existing domain projects remain authoritative; MathEvidence integrates them
  instead of replacing them.

## Documentation

| Doc | Role |
| --- | --- |
| [`docs/README.md`](docs/README.md) | Documentation landing / table of contents |
| [`docs/getting-started/`](docs/getting-started/) | Install, check, Agent API, first replay |
| [`docs/STATUS.md`](docs/STATUS.md) | Public-preview status |
| [`docs/security/KNOWN_TRUST_GAPS.md`](docs/security/KNOWN_TRUST_GAPS.md) | Known limitations |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Delivery order |
| [`docs/SPEC_INDEX.md`](docs/SPEC_INDEX.md) | Full specification map |

## Repository map

- `MathEvidence/` — Lean semantics, protocol types, encodings, checkers,
  tactics, registry interfaces, tests
- `adapters/` — untrusted solver adapters (Mathematica via `wolframscript` or
  offline fixtures; SageMath/SymPy open references; LeanLink scaffold until
  [`docs/architecture/leanlink-adapter-review.md`](docs/architecture/leanlink-adapter-review.md)
  closes)
- `agent/` — AI-facing operation API and SDKs (public bundle access by
  **`bundleId` only**)
- `studio/` — Mathematica notebook and editor experiences
- `foundry/` — schemas and pipelines for certified tool-use episodes
- `registry/` — machine-readable capability and backend declarations
  (capabilities stay `experimental` until governance gates pass)
- `benchmarks/` — real-world, adversarial, and conformance suites
- `evidence/` — committed Evidence Bundle trees (schema **v0.2** `.cjson`)
- `docs/` — specifications, products, RFCs, ADRs, trust model, status

## First implementation wedge

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
only. It does not establish Mathlib `HasDerivAt` / analytic ODE theorems.
Analytic fragments live under the separate experimental id
`analysis.analytic_calculus`.

**Dual-backend evidence:** `algebra.rational_equality` has SymPy live generation
plus Mathematica live generation via `wolframscript` when
`MATHEVIDENCE_WOLFRAMSCRIPT` is set (public CI without Wolfram uses committed
offline fixtures). Sage rational support is **declared/placeholder only**.
Linear algebra and finite counterexample have SymPy `conformance_verified`.
See `registry/` and [`docs/STATUS.md`](docs/STATUS.md).

The architectural target is that each capability support Mathematica and at
least one open backend while using one shared Lean checker per claim type.

## Build and test

Prerequisites: Lean toolchain matching `lean-toolchain`, Python 3 with the repo
requirements files, and [`just`](https://github.com/casey/just).

```text
just check
```

Focused trust subset:

```text
pytest tests/forensic -q
```

Agent API (local):

```text
python -m agent.api.server --host 127.0.0.1 --port 8787
```

See [`docs/getting-started/`](docs/getting-started/) and
[`agent/README.md`](agent/README.md). Open/inspect/replay take opaque `bundleId`
values from the content-addressed store — not filesystem paths.

**CI honesty:** workflow definitions exist under `.github/workflows/`. Immutable
green runs on a release commit are not attested in-repo. Do not treat local
`just check` as promotion evidence.

## Not yet

- Live federation with external projects (fixtures only).
- Completed human gates (external confirmations, dual-area stable review,
  Studio usability results).
- Lean toolchain bump beyond the committed pin.
- Any capability marked `"stable"`.
- Production receipt PKI (dev-only crypto under `dev/receipt-keys/`).

## Delivery rule

The project does not generalize the protocol in anticipation of future domains.
New abstractions are admitted only after two independent domain implementations
demonstrate the common requirement.

See [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md) for the normative
specification, [`docs/REPOSITORY_ARCHITECTURE.md`](docs/REPOSITORY_ARCHITECTURE.md)
for monorepo design, [`docs/STATUS.md`](docs/STATUS.md) for preview status, and
[`docs/release/RELEASE_NOTES_DRAFT.md`](docs/release/RELEASE_NOTES_DRAFT.md)
for the public-preview notes draft.
