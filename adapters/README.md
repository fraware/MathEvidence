# Adapters (Python)

Untrusted backend adapters. Protocol: JSON-RPC over stdio (ADR 0003).

## Packages

| Package | Role |
| --- | --- |
| `adapters/common` | Framing, canonical digests, schema validation, resource limits, errors |
| `adapters/sympy` | Open v0 backend for `algebra.rational_equality` |
| `adapters/mathematica` | Closed v0 backend (live or fixture); LeanLink scaffold |
| `adapters/sage` | Optional third open backend (fixture mode when Sage missing) |

## Install

Prefer uv when TLS/network works:

```text
uv lock
uv sync --extra dev --extra sympy
```

If `uv.lock` is missing due to TLS failures (`UnknownIssuer`), use pip:

```text
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

## Run SymPy adapter (JSON-RPC NDJSON on stdio)

```text
python -m adapters.sympy
```

Orchestration CLI (compute + optional EvidenceBundle write):

```text
python scripts/mathevidence_cli.py compute --backend sympy --request path/to/request.json --bundle-dir evidence/tmp/demo
```

Discovery (adapter → bundle; Lean uses this when `MATHEVIDENCE_DISCOVERY=1`):

```text
python scripts/mathevidence_cli.py discover --backend sympy --request path/to/request.json --bundle-dir out/ --direct
```

See `docs/architecture/discovery.md`.

## Conformance

```text
python scripts/generate_evidence_fixtures.py   # regenerate fixtures
python scripts/run_adapter_conformance.py
python scripts/offline_replay_python.py
python -m pytest adapters -q
```

## Mathematica

See [`adapters/mathematica/README.md`](mathematica/README.md). Default CI uses fixture mode;
committed evidence under `evidence/` must replay without Mathematica.

## SageMath

See [`adapters/sage/README.md`](sage/README.md). Optional third backend; CI defaults to fixture mode
when `sage` is not installed.
