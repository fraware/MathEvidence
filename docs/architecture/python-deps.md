# Dependency lock status (ME-RV-070)

## Authoritative path

Committed `uv.lock` + `uv sync --frozen` in CI is required.

```text
uv lock
uv sync --frozen --extra dev --extra sympy
```

Workflow: `.github/workflows/uv-lock.yml` (ubuntu-latest, SHA-pinned
`astral-sh/setup-uv`). Lean, release, offline-replay, adapter, adversarial,
security, and benchmarks workflows all require `uv.lock` and run
`uv sync --frozen`.

## Local Windows TLS gap

On some maintainer Windows environments `uv lock` fails with:

```text
invalid peer certificate: UnknownIssuer
```

even with `uv lock --native-tls`. That does **not** waive the lockfile
requirement. Generate `uv.lock` from CI (`workflow_dispatch` on `uv-lock.yml`,
download the `uv-lock` artifact) or from a Linux/macOS machine with working
PyPI TLS, then place it at the repository root.

## Compatibility freeze

```text
python scripts/freeze_requirements.py
```

writes `requirements-freeze.txt` from the active interpreter for diagnostic
compatibility only. It is **not** a substitute for committed `uv.lock`.
