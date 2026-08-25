# Required workflows (CI dimensions)

Distinct job names / workflows map to independent maturity dimensions:

| Dimension | Workflow / job |
| --- | --- |
| `benchmark-task-suite` | `benchmarks.yml` job `benchmark-task-suite` |
| `adapter-conformance` | `adapter-conformance.yml` |
| `assurance-exact-replay` | `assurance-exact-replay.yml` |
| `offline-replay` | `offline-replay.yml` (Python exact bundle + Lean fixtures leg) |
| `replay-tamper` | `replay-tamper.yml` |
| `security-bounded-execution` | `security.yml` job `security-bounded-execution` |
| `supply-chain` | `supply-chain.yml` |
| `lean-assurance-audit` | `lean-assurance-audit.yml` (Python); Lake build remains `lean.yml` |

Also present: `release.yml`, `uv-lock.yml`.

Normative behavior is specified in `docs/TESTING_AND_CI.md`.
Operator CI triage map: `docs/HANDOFF.md`.

These workflow definitions are present and their third-party actions are pinned
to immutable commit SHAs with the intended action version kept as an inline
comment. This repository documentation does not attest an immutable green CI run
for the audit baseline; branch protection must still be enabled by a repository
administrator using `docs/validation/ci-branch-protection.md`.

Release-grade ideal membership (`benchmarks.yml` / `ideal-release-grade`) may
depend on exact replay, but logs distinguish Lake/setup failures from benchmark
logic failures. Benchmark scores never write `crEligible`.
