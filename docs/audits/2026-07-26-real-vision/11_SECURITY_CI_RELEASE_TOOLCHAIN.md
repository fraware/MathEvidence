# Standalone specification — security, CI, release, and reproducibility


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Required CI posture

Protect `main`. Require pull requests and required checks. Direct pushes to trust-path files must be disabled.

Required checks:

- Lean build;
- executable build;
- kernel replay;
- import graph;
- axiom policy;
- schema validation;
- registry validation;
- Python lint, format, typing, tests;
- forensic suite;
- adapter conformance;
- bundle migration;
- ideal membership smoke;
- adversarial suite;
- supply-chain scan;
- dependency review;
- release provenance dry run.

## Reproducible dependencies

- Commit `uv.lock`.
- Use `uv sync --frozen`.
- Remove optional-lock language from requirements docs.
- Generate `requirements-freeze.txt` from the lock for compatibility only.
- SHA-pin `astral-sh/setup-uv`.
- Pin the Lean toolchain and Mathlib revision, already done.
- Replace mutable elan installer download with a checksum-pinned release asset or SHA-pinned setup action.
- Pin all GitHub actions by commit.

## Trust-boundary audit

Replace regex-only import checks with a Lean environment-aware tool.

The tool must:

- enumerate imported modules for every trusted root;
- identify imports of Tactic, Agent, adapters, IO/process/network modules;
- fail on forbidden dependencies;
- cover Core, IR, Encoding, and Checkers;
- output a machine-readable graph.

Retain source scanning as defense in depth.

## Axiom audit

Implement environment-level axiom reporting for every exported theorem in checker soundness and generated certifications.

Required output:

- declaration;
- theorem type digest;
- imported axioms;
- classical/propext/quotient markers;
- project-specific axioms;
- unsafe/native dependencies;
- environment lock.

CI must fail on:

- `sorryAx`;
- project-specific axiom;
- unexpected unsafe declaration in trusted packages;
- missing report.

The current source scanners must immediately expand to Encoding, Hypothesis, Conjecture, TraceToPlan, Assurance, and all root modules until the environment audit replaces them.

## Executable gate

`lake build` must explicitly build:

- `mathevidence-verify-bundle`;
- `mathevidence-kernel-replay`;
- import audit;
- axiom report.

`just check` must execute each executable against positive and negative fixtures.

## Forensic suite

Move all trust-path forensic tests into required CI. Include:

- joint request/certificate forgery;
- duplicate keys;
- content substitution;
- theorem substitution;
- receipt forgery;
- path jail;
- symlink/race tests;
- digest parity;
- status overclaim;
- environment mismatch;
- content-address collision.

## Resource isolation

External adapters must run in isolated subprocesses with:

- fixed argv;
- no shell;
- wall, CPU, memory, and output limits;
- cancellation followed by process-group termination;
- sanitized environment;
- isolated temporary directory;
- no inherited secrets;
- network disabled by default.

## Release

A release workflow must:

1. run all required checks on the tag commit;
2. build Lean packages and executables;
3. build Python wheel/sdist;
4. generate SBOM;
5. generate provenance;
6. generate artifact digests;
7. sign artifacts with the release key;
8. create a GitHub prerelease;
9. upload artifacts and verification instructions;
10. publish only after human release approval.

The first release remains `0.x` experimental.

## Branch protection evidence

Store a dated machine-readable report under `docs/validation/ci/` containing:

- commit SHA;
- required checks;
- workflow run IDs;
- conclusions;
- branch protection settings;
- reviewer identities.

## Acceptance

The exact released commit must have a complete green check set. Dependency resolution must be frozen. Trust and axiom audits must inspect Lean’s environment, not only source text.
