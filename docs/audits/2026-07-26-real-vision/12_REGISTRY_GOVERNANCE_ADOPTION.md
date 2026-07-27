# Standalone specification — registry, governance, and adoption


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Registry as executable truth

The registry must be the single source for:

- capability ID and version;
- lifecycle;
- claim classes;
- request and evidence schemas;
- checker package and theorem;
- supported adapters;
- routing status;
- assurance mode;
- conformance artifact;
- known limitations;
- owner teams.

Generate Agent routing and support matrices from registry data.

## Capability naming

- Keep `algebra.rational_equality`.
- Keep `algebra.formal_rational_calculus`.
- Keep `analysis.analytic_calculus`.
- Rename `algebra.ideal_membership_witness` to `algebra.ideal_membership_witness` unless a genuine Gröbner certificate is implemented.
- Deprecate stale `analysis.symbolic_calculus` with an explicit migration record.

## Lifecycle states

Use:

- `experimental`
- `candidate`
- `stable`
- `deprecated`
- `retired`

`candidate` means checker soundness and end-to-end kernel replay exist, but adoption or governance gates remain.

## Stable promotion record

Add `schemas/promotion-record.schema.json`.

A stable capability requires a signed promotion record containing:

- capability/version;
- release commit;
- complete CI attestation;
- checker soundness theorem;
- kernel replay examples;
- conformance digest;
- domain review;
- trust review;
- security review;
- three user confirmations;
- one external workflow win;
- one external adoption;
- owner teams;
- deprecation policy;
- known limitations.

`validate_registry.py` must verify the record. Documentation checkboxes alone are insufficient.

## Maintainer teams

Create real GitHub teams for:

- Core/trust;
- Semantic IR/encoding;
- Domain checkers;
- Adapters;
- Agent/Studio;
- Foundry/benchmarks;
- Security/release;
- Docs/governance.

Trust-path changes require Core/trust plus domain or security approval. One person in multiple teams does not satisfy independent-area review for stable promotion.

## External validation

Run structured interviews with at least three non-maintainer Lean users.

Capture:

- project and role;
- current computational bottleneck;
- existing workaround;
- exact MathEvidence capability used;
- time or proof-complexity impact;
- semantic or trust concerns;
- consent to quote or anonymize.

A workflow win requires an actual theorem or development change, not agreement that the problem exists.

## Adoption

One external project must:

- consume a released MathEvidence package;
- use a capability in its own repository;
- replay evidence without a backend;
- record integration feedback;
- identify a maintainer contact.

## Stable freeze

No capability may be stable until all technical and human gates pass. Rational equality may reach candidate first. Ideal membership should be the first target for a value-bearing stable capability after adoption.

## Acceptance

Registry status, runtime routing, release artifacts, and governance records must agree. Stable status must be mechanically impossible without the signed promotion record.
