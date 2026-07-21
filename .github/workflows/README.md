# Required workflows

The implementation repository must provide:

- `lean.yml`
- `offline-replay.yml`
- `adapter-conformance.yml`
- `adversarial.yml`
- `benchmarks.yml`
- `security.yml`
- `supply-chain.yml`
- `release.yml`

Their normative behavior is specified in `docs/TESTING_AND_CI.md`.

These workflow definitions are present and their third-party actions are pinned
to immutable commit SHAs with the intended action version kept as an inline
comment. This repository documentation does not attest an immutable green CI run
for the audit baseline; branch protection must still be enabled by a repository
administrator using `docs/validation/ci-branch-protection.md`.
