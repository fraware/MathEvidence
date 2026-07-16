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

### 2.3 Differential backend tests

Mathematica and an open backend receive the same requests. Outcomes are classified as:

- both produce accepted evidence;
- one succeeds and one reports unsupported;
- one produces rejected evidence;
- or semantic disagreement.

Disagreement is never automatically resolved in favor of a backend.

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

## 3. CI workflows

### `lean.yml`

Runs on every pull request:

- Lake build;
- formatting and linting;
- unit tests;
- import-boundary checks;
- `sorry` scan;
- axiom audit;
- documentation consistency.

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

Runs malformed inputs, fuzz seeds, and resource-limit tests.

### `benchmarks.yml`

Nightly workflow runs real-world benchmarks and publishes performance trends. Benchmark regression is informative initially and becomes blocking after stable budgets are established.

### `security.yml`

Runs dependency review, static analysis, secret scanning, and native-component checks.

### `release.yml`

Builds source and package artifacts, verifies clean replay, generates provenance, signs artifacts, and publishes release notes containing schema and assurance changes.

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
