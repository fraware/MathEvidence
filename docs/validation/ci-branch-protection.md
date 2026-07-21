# CI Branch Protection Requirements

Branch protection is a GitHub repository setting and cannot be enforced by files
in this repository. A repository administrator must enable it in GitHub after the
workflows exist and have produced the expected check names.

## Required settings

- Require a pull request before merging to `main`.
- Require status checks to pass before merging.
- Require branches to be up to date before merging when GitHub offers that
  option for the repository.
- Require conversation resolution before merging.
- Restrict direct pushes to trusted maintainers or disallow them entirely.

## Required checks

Enable these workflow checks as required for `main`:

- `lean / lean`
- `offline-replay / offline-replay`
- `adapter-conformance / sympy-conformance`
- `adversarial / adversarial-seed`
- `security / security`
- `supply-chain / gitleaks`

For release tags, keep `release / release-provenance` as the provenance gate.
For benchmark-sensitive changes, require `benchmarks / benchmarks` or run it
manually before merge when the pull request does not match the workflow path
filters.

## Audit honesty

The repository now contains CI definitions and pinned action references, but
that is not the same as an immutable green CI baseline. Record the exact commit
SHA and GitHub run URLs in release or audit notes only after GitHub has executed
these required checks successfully.
