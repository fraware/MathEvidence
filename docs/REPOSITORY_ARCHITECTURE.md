# MathEvidence Monorepo Architecture

This document is normative. The repository structure exists to enforce trust boundaries and ownership boundaries. Directory placement is not cosmetic.

## 1. Top-level layout

```text
mathevidence/
├── README.md
├── LICENSE
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── GOVERNANCE.md
├── SECURITY.md
├── SUPPORT.md
├── ROADMAP.md
├── lakefile.toml
├── lean-toolchain
├── pyproject.toml
├── uv.lock
├── justfile
├── .editorconfig
├── .gitignore
├── .github/
│   ├── CODEOWNERS
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
├── MathEvidence/
│   ├── Core/
│   ├── IR/
│   ├── Checkers/
│   ├── Tactic/
│   ├── Registry/
│   └── Testing/
├── adapters/
│   ├── common/
│   ├── mathematica/
│   ├── sage/
│   └── sympy/
├── agent/
│   ├── api/
│   └── sdk/
├── studio/
│   ├── wolfram/
│   └── vscode/
├── foundry/
│   ├── schema/
│   └── pipelines/
├── registry/
│   ├── capabilities/
│   └── backends/
├── benchmarks/
│   ├── real_world/
│   ├── adversarial/
│   └── conformance/
├── evidence/
│   ├── examples/
│   └── conformance/
├── examples/
├── schemas/
├── docs/
│   ├── products/
│   ├── architecture/
│   ├── rfcs/
│   ├── adr/
│   └── threat-model/
├── scripts/
└── tools/
```

## 2. Lean package boundaries

### `MathEvidence/Core`

Owns only solver-independent concepts:

- claim classes;
- result status;
- evidence identifiers;
- assurance modes;
- provenance records;
- capability identifiers;
- bundle metadata;
- stable error codes.

Core MUST have no domain-specific mathematics and no process, file-system, network, JSON, or adapter dependency unless the relevant parser is itself part of a theorem-level verified path.

### `MathEvidence/IR`

Owns typed, restricted mathematical languages and their Lean semantics.

Recommended structure:

```text
IR/
├── Common/
│   ├── Identifier.lean
│   ├── Version.lean
│   └── Hash.lean
├── RationalExpr/
│   ├── Syntax.lean
│   ├── Eval.lean
│   ├── Reify.lean
│   ├── Soundness.lean
│   └── Serialize.lean
├── MatrixExpr/
└── FinitePredicate/
```

A domain IR MUST expose:

- syntax;
- typed interpretation;
- reification;
- semantic correspondence theorem;
- canonical serialization;
- size measure;
- and rejection behavior.

A universal expression AST is forbidden in the first release.

### `MathEvidence/Checkers`

Owns candidate and certificate structures, checkers, and soundness theorems.

```text
Checkers/
├── RationalEquality/
├── LinearAlgebra/
├── Counterexample/
├── Polynomial/
└── Shared/
```

Each checker directory MUST contain:

- `Spec.lean` — mathematical claim;
- `Certificate.lean` — evidence type;
- `Check.lean` — executable checker;
- `Soundness.lean` — proof of checker soundness;
- `Replay.lean` — bundle replay interface;
- `Tests.lean` — positive and negative fixtures;
- `README.md` — claim strengths and limitations.

Checkers MUST NOT invoke external processes.

### `MathEvidence/Tactic`

Owns Lean elaborator and tactic UX.

It MAY invoke adapter orchestration in discovery mode. It MUST support a pure replay mode where evidence is already present. It MUST display explicit assumptions, status, backend, claim class, and assurance mode.

### `MathEvidence/Registry`

Owns Lean-side capability lookup and validation of registry declarations. It MUST distinguish declared support from verified conformance.

### `MathEvidence/Testing`

Owns reusable generators, adversarial fixtures, semantic oracles for bounded domains, and common conformance assertions. Production packages MUST NOT depend on heavy testing utilities.

## 3. Adapter boundaries

Adapters are untrusted provider implementations. They do not contain theorem-level soundness logic.

### `adapters/common`

Contains:

- JSON-RPC message models;
- canonical JSON utilities;
- process lifecycle helpers;
- resource limit wrappers;
- test harnesses;
- and capability negotiation helpers.

### `adapters/mathematica`

Contains a Wolfram paclet or package layered on LeanLink.

Responsibilities:

- decode a MathEvidence request;
- map the supported semantic IR to Wolfram Language expressions;
- invoke exact Mathematica operations;
- construct solver-independent candidate and evidence objects;
- report all introduced conditions;
- record Mathematica, Wolfram Language, LeanLink, and adapter versions;
- and pass backend conformance tests.

It MUST NOT mark a result certified. Only Lean replay can do so.

### `adapters/sage` and `adapters/sympy`

Provide open generation paths and differential testing. At least one must support every stable v0 capability.

## 4. Agent subsystem

### `agent/api`

Contains OpenAPI or equivalent schemas, a thin orchestration server, and operation definitions. The server is not part of theorem replay.

### `agent/sdk`

Contains typed clients for Python and, only when demanded, other languages. SDKs expose operation-level tools and stable error codes.

The agent subsystem MUST NOT expose unrestricted shell execution as a MathEvidence operation.

## 5. Studio subsystem

### `studio/wolfram`

Builds on LeanLink and provides:

- `CertifyInLean`;
- visible assumptions and claim strength;
- evidence status badges;
- theorem export;
- and bundle inspection.

The notebook interface MUST visually distinguish computed, tested, witness-verified, complete, and approximation-certified results.

### `studio/vscode`

Provides code lenses, status views, evidence inspection, and capability discovery. It must remain a client of stable APIs and contain no unique semantics.

## 6. Foundry subsystem

Foundry code records and transforms execution episodes after theorem decisions have occurred. It never participates in acceptance.

- `schema/` contains versioned episode schemas.
- `pipelines/` contains extraction, validation, de-identification, deduplication, quality scoring, and dataset split logic.

Raw user code or proprietary solver output MUST NOT be published without explicit licensing and privacy review.

## 7. Registry data

Registry data is version-controlled, schema-validated, and conformance-backed.

A capability file identifies:

- operation;
- schema version;
- supported domain;
- claim classes;
- evidence format;
- checker module;
- assurance modes;
- deterministic limits;
- known limitations;
- and conformance suite.

A backend file identifies:

- executable or runtime;
- adapter version;
- supported capability versions;
- license requirements;
- reproducibility status;
- and conformance results.

No capability may be marked `stable` from documentation alone.

## 8. Benchmarks

### `real_world`

Curated from active formalization bottlenecks. Each task records the current workaround and why external computation is materially useful.

### `adversarial`

Contains semantic traps, malformed evidence, digest mismatch, omitted conditions, coercion mistakes, branch ambiguities, and resource attacks.

### `conformance`

Backend-independent expected requests and acceptable evidence behavior.

Benchmark files are immutable after release. Corrections create a new benchmark version.

## 9. Evidence directory

Only small, legally distributable evidence bundles are committed.

Rules:

- Every bundle passes offline replay.
- Generated certificates are content-addressed.
- Backends are disabled in replay CI.
- Large evidence lives in release assets or an artifact store with immutable digests.
- Evidence is never edited in place.

## 10. Documentation

- `docs/products/` contains one standalone specification per product.
- `docs/rfcs/` contains proposed cross-cutting changes.
- `docs/adr/` contains accepted architectural decisions.
- `docs/threat-model/` contains security analyses by boundary.
- `docs/architecture/` contains explanatory diagrams and dependency rules.

Documentation is reviewed as code. A behavior change without a corresponding normative documentation update is incomplete.

## 11. Dependency direction

The allowed dependency graph is:

```text
Core
  ↑
IR
  ↑
Checkers
  ↑
Tactic / Registry
  ↑
Examples and applications

Adapters ──> protocol schemas only
Agent    ──> orchestration and registry
Studio   ──> orchestration and LeanLink
Foundry  ──> execution records and bundles
```

Forbidden edges include:

- Core → adapter
- Checker → backend process
- Checker → notebook
- Mathlib-facing theorem → proprietary runtime
- Foundry → acceptance decision
- Studio → unique mathematical semantics

CI MUST include an import-boundary check.

## 12. Technology choices

### Lean

- The project pins a stable Lean toolchain.
- Mathlib revision is explicit and updated through controlled migration pull requests.
- Lake is the authoritative Lean build system.

### Adapter implementation

- JSON-RPC over stdio is the v0 transport.
- Python adapters use Python 3.12+, `uv`, `ruff`, `mypy`, and `pytest`.
- The Mathematica adapter uses a paclet layered on LeanLink and Wolfram testing infrastructure.
- A persistent daemon is deferred until benchmarks demonstrate process startup is a material bottleneck.

### Serialization

- Control-plane artifacts use canonical JSON compatible with RFC 8785 principles.
- SHA-256 is the mandatory digest in v0.
- Domain certificates may use binary encodings only with a versioned schema, size limits, and a Lean decoder path.

### Developer tooling

- `just` supplies repository commands.
- Pre-commit hooks are optional conveniences; CI is authoritative.
- A dev container MAY be supplied, while pinned language toolchains remain primary.

## 13. Branch and release policy

- `main` is always releasable.
- Feature branches are short-lived.
- Protocol changes require RFC and architecture approval.
- Releases sign source archives and evidence manifests using a transparent signing mechanism.
- Release notes list assurance changes, schema changes, checker changes, and replay compatibility.

## 14. Code ownership

CODEOWNERS SHOULD require specialist review for:

- `Core` and trust model;
- each domain checker;
- adapter security;
- Agent API schemas;
- Foundry licensing and privacy;
- and release workflows.

No individual should be able to merge a change that simultaneously alters a checker, its soundness theorem, and the corresponding conformance expectation without independent review.
