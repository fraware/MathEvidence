# Mathematica / LeanLink adapter

Closed v0 backend for `algebra.rational_equality` (RFC 0001). Evidence contract
matches the SymPy adapter: candidate numerator + denominator factors +
provenance — never a trusted Boolean.

## Modes

| Mode | When | Behavior |
| --- | --- | --- |
| `fixture` | Default when Wolfram is missing, or `MATHEVIDENCE_ADAPTER_MODE=fixture` | JSON-RPC works; `compute` returns `backend_unavailable` |
| `live` | `wolframscript`/`math` found, or `MATHEVIDENCE_WOLFRAMSCRIPT` set | Spawns fixed-argv subprocess (no shell interpolation) |

Committed evidence under `evidence/` must always replay offline without
Mathematica. Public CI uses fixture / replay paths.

## Environment

| Variable | Purpose |
| --- | --- |
| `MATHEVIDENCE_WOLFRAMSCRIPT` | Absolute path to `wolframscript` (preferred) |
| `MATHEVIDENCE_LEANLINK` | Path to LeanLink install (scaffold; unused for theorem acceptance) |
| `MATHEVIDENCE_ADAPTER_MODE` | `fixture` or `live` |

## Run

```text
# Fixture / CI
python -m adapters.mathematica

# Live (licensed host)
set MATHEVIDENCE_WOLFRAMSCRIPT=C:\Path\To\wolframscript.exe
python -m adapters.mathematica
```

JSON-RPC is newline-delimited JSON over stdio (same as SymPy).

## LeanLink scaffold

LeanLink / LibraryLink remains **outside** the theorem TCB
(`docs/architecture/leanlink-adapter-review.md`). This package:

1. Discovers LeanLink via `MATHEVIDENCE_LEANLINK` and reports it on `initialize`.
2. Uses `wolframscript -code <script>` with an allow-listed environment.
3. Does **not** load native LeanLink bridges in CI.
4. Accepts only a narrow live IR decode scaffold (zero-numerator identities);
   richer WL→RationalExpr mapping lands with the paclet.

## Offline evidence

Generate with SymPy (or live Mathematica on a licensed machine), commit the
bundle under `evidence/examples/` or `evidence/conformance/`, then verify with:

```text
python scripts/offline_replay_python.py
```

Replay never starts Mathematica.
