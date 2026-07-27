# Standalone specification — Foundry, benchmarks, and federation


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Foundry quality tiers

Redefine Q2:

```text
Q2_formally_verified =
  immutable candidate bundle
  + verified certification record
  + exact theorem/refutation identity
  + environment lock
  + passing axiom policy
```

Python mirror acceptance, generated counterexample metadata, and checker-only results are Q1 or a new `Q1_checker_preview` tier.

Rebuild the corpus after applying this definition.

## Provenance

Every release manifest must contain an immutable Git commit SHA. `sourceCommit: workspace` is forbidden in published releases.

Every episode must include:

- source family;
- capability/version;
- request digest;
- candidate bundle ID;
- certification record ID when Q2;
- backend;
- theorem declaration;
- environment lock;
- license provenance;
- generated/synthetic flag;
- contamination labels.

## Corpus statistics

Report both raw and family-normalized counts. A campaign with hundreds of near-isomorphic FiniteGraph episodes must not imply hundreds of independent domains.

Required statistics:

- episodes by capability;
- episodes by source family;
- unique normalized claim shapes;
- Q2 with independent theorem;
- backend diversity;
- coefficient/domain diversity;
- train/eval family overlap;
- human-reviewed counts.

## Benchmark rules

Each benchmark has four independent outcomes:

1. backend proposal;
2. decoder acceptance;
3. checker acceptance;
4. theorem certification.

A benchmark must never substitute an expected witness for the backend proposal when calculating backend success.

## Benchmark integration

Add fast required tiers to `just check`:

- rational conformance;
- ideal membership smoke;
- linear algebra smoke;
- counterexample smoke;
- kernel replay smoke;
- forensic receipt/bundle tests.

Add nightly scale tiers:

- full ideal membership;
- differential Mathematica/Sage;
- Foundry evaluation;
- performance sweeps;
- fuzzing.

Workflow path filters must include checker, IR, encoding, adapter, schema, and registry changes affecting a benchmark.

## Held-out evaluation

Create an external-project held-out set with explicit permissions and provenance. At minimum:

- five Mathlib-derived algebra obligations;
- five scientific/analytic obligations from SciLean or Physlib where appropriate;
- five computer-science obligations from CSLib or related finite structures;
- five independent contributor problems.

Do not claim adoption from copied examples. Adoption requires an external maintainer or contributor using the component in their workflow.

## Federation

Fixture metadata remains `fixture_only`.

Live federation requires:

- signed agreement;
- capability/version;
- exact emitted/consumed roles;
- status mapping;
- digest algorithm;
- threat model;
- maintainer contacts;
- conformance suite;
- revocation procedure.

At least two external projects must emit or consume real metadata before federation milestone closure.

## Data licensing

Do not redistribute proprietary Mathematica outputs beyond licensed and reviewed artifact forms. Store minimal normalized certificates where permitted. Document provenance and redistribution rights for every non-MathEvidence source.

## Acceptance

A Foundry release may claim Q2 only for replayable kernel-certified episodes. Benchmark success must reflect actual backend output. Federation may be called live only when external peer integrations run in CI or independently recorded conformance.
