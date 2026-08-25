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
| `lean` | `lean.yml` (Lake build, declaration-identity, audits) |

Also present: `release.yml`, `uv-lock.yml`, `adversarial.yml`.

Normative behavior is specified in `docs/TESTING_AND_CI.md`.
Operator CI triage map: `docs/HANDOFF.md`.
Public status / CR eligibility: `docs/STATUS.md`.

These workflow definitions are present and their third-party actions are pinned
to immutable commit SHAs with the intended action version kept as an inline
comment. This repository documentation does not attest an immutable green CI run
for a release commit; branch protection must still be administered using
`docs/validation/ci-branch-protection.md`.

Release-grade ideal membership (`benchmarks.yml` / `ideal-release-grade`) may
depend on exact replay, but logs distinguish Lake/setup failures from benchmark
logic failures. Benchmark scores never write `crEligible`.

A green `benchmark-task-suite` with a red `assurance-exact-replay` or `lean`
job is **not** "assurance green."
