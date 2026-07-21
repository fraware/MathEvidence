# Testing and Continuous Integration Specification

## 1. Testing philosophy

MathEvidence is tested as an assurance system, not merely as a software library. Correct acceptance and correct rejection carry equal importance.

## 2. Test layers

### 2.1 Lean unit tests

- syntax and interpretation;
- reification success and rejection;
- checker positive cases;
- checker negative cases;
- claim-strength transitions;
- request binding;
- provenance validation;
- replay behavior.

### 2.2 Property-based tests

Bounded generators test:

- reify/evaluate correspondence;
- canonical serialization stability;
- alpha-renaming invariance;
- permutation invariance where mathematically appropriate;
- evidence mutation rejection;
- and backend-independent candidate verification.

Harness: `adapters/common/test_property.py` (Hypothesis) via
`scripts/run_property_tests.py` / `just property` (part of `just check`).

### 2.2b Metamorphic tests

Variable rename, reassociation, and redundant assumptions must preserve
accept/reject for rational equality.

Harness: `scripts/run_metamorphic.py` / `just metamorphic`.

### 2.3 Differential backend tests

Mathematica and an open backend receive the same requests. Outcomes are classified as:

- both produce accepted evidence;
- one succeeds and one reports unsupported;
- one produces rejected evidence;
- or semantic disagreement.

Disagreement is never automatically resolved in favor of a backend.

Harness: `scripts/run_differential_backends.py` (writes
`benchmarks/differential/manifest.json`; retains disagreements under
`benchmarks/differential/disagreements/`). When Wolfram is absent, Mathematica
rows are labeled `skip` / `fixture`. Run via `just differential` (part of
`just check`).

### 2.4 Adversarial semantic tests

Required cases include:

- denominator equal to zero;
- integer/rational/real coercion changes;
- strict versus non-strict inequalities;
- variable shadowing;
- swapped matrix dimensions;
- transposed indexing;
- hidden branch assumptions;
- candidate valid on a proper subdomain;
- incomplete solution families;
- and exact claims derived from approximate data.

### 2.5 Malformed evidence tests

- wrong request hash;
- truncated certificate;
- duplicate keys;
- unknown schema version;
- excessive nesting;
- oversized integer;
- path traversal;
- malicious file name;
- and certificate for a different capability.

Executable runner (beyond seed catalog validation):
`scripts/run_adversarial_executable.py` / `just adversarial-exec`, also wired in
`security.yml` and `adversarial.yml`.

### 2.6 Performance tests

Every stable capability defines budgets for:

- request reification;
- backend generation;
- evidence size;
- decoder time;
- checker time;
- memory;
- and downstream Lean build time.

Regressions beyond the declared budget require explicit approval.

Budgets live in registry capability JSON as `perfBudgets`. Runner:
`scripts/run_perf_budgets.py` / `just perf-budgets` (fails CI on regression for
measured capabilities). Isolation limits:
`docs/architecture/process-isolation.md`.

## 3. CI workflows

### `lean.yml`

Runs on every pull request:

- Lake build;
- formatting and linting;
- unit tests;
- compiled trust-audit executables (`mathevidence-import-graph` and
  `mathevidence-axiom-report`);
- documentation consistency.

The compiled trust-audit executables are authoritative when available. They are
currently honest compiled drivers over Lean source scans, not full Lean
environment audits; the Python scripts under `scripts/` are supplemental
regex-only fallbacks.

### `offline-replay.yml`

Runs with backend executables unavailable. Rechecks every committed evidence bundle and example theorem.

This workflow is merge-blocking.

### `adapter-conformance.yml`

Runs a backend matrix:

- SageMath;
- SymPy;
- Mathematica on a licensed self-hosted runner when available.

Mathematica generation is not required for ordinary open-source pull requests. Stored Mathematica evidence must still replay publicly.

### `adversarial.yml`

Runs malformed inputs, fuzz seeds, and resource-limit tests
(`validate_adversarial_seed.py` + `run_adversarial_executable.py`).

### `benchmarks.yml`

Nightly workflow runs real-world benchmarks, property/metamorphic suites, and
performance budgets. Perf budget regressions are blocking when `perfBudgets` are
declared.

### `security.yml`

Runs dependency review, static analysis, secret scanning, executable adversarial
resource cases, and cancel→kill isolation tests.

### `supply-chain.yml`

Runs a blocking gitleaks secret scan with immutable action pins. Dependency
review remains in `security.yml`.

### `release.yml`

Builds source and package artifacts, verifies clean replay, generates a
provenance manifest (evidence digests + Lean toolchain / lake commit pins), and
uploads it as a release artifact. Signing/publish remain governance-gated.

## 4. Pull-request gates

A PR modifying a stable checker must include:

- updated positive and negative tests;
- soundness proof preservation;
- adversarial mutation tests;
- benchmark impact;
- and explicit assurance review.

A PR modifying a request or evidence schema must include:

- compatibility analysis;
- migration path;
- registry update;
- conformance updates;
- and bundle replay tests.

## 5. Benchmark methodology

Every benchmark task records:

- mathematical source;
- current Lean-only approach;
- reason external computation is useful;
- expected claim strength;
- permitted assumptions;
- and contamination status.

Evaluation reports:

- success rate;
- semantic error rate;
- unsupported rate;
- backend generation cost;
- checking cost;
- total human interventions;
- and Lean-only baseline.

A task solved by ordinary Lean automation with comparable cost is not evidence of MathEvidence impact.
