# Dependency lock status

`uv.lock` is **not** committed yet. Local/CI attempts to run `uv lock` fail with:

```text
invalid peer certificate: UnknownIssuer
```

even with `uv lock --native-tls` on this Windows environment.

## Robust install path (authoritative for `just check`)

```text
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pip install -e .
just check
```

Pinned minimums live in `requirements.txt` / `requirements-dev.txt` and
`pyproject.toml`. Prefer generating and committing `uv.lock` once PyPI TLS
works on the maintainer machine or in CI:

```text
uv lock --native-tls
uv sync --extra dev --extra sympy
```

Do not claim a lockfile exists until that succeeds and the file is committed.
