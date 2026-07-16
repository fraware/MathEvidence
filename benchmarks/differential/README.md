# Differential backend benchmarks

Harness: `scripts/run_differential_backends.py` (TESTING_AND_CI.md §2.3).

Identical `algebra.rational_equality` requests from
`evidence/conformance/rfc0001/` are evaluated on SymPy (always live) and
Mathematica (live when `MATHEVIDENCE_WOLFRAMSCRIPT` is set; otherwise
`fixture` / `skip` with clear labels).

## Policy

Disagreement is **never** auto-resolved in favor of a backend. Semantic
disagreements are written under `disagreements/` and fail the harness exit
code.

## Run

```text
# CI / no Wolfram (SymPy live + Mathematica skip/fixture)
python scripts/run_differential_backends.py

# Live Mathematica + SymPy
set MATHEVIDENCE_WOLFRAMSCRIPT=C:\Path\To\wolframscript.exe
python scripts/run_differential_backends.py
```

`just differential` runs the same script. It is part of `just check`.

## Artifacts

| Path | Role |
| --- | --- |
| `manifest.json` | Last run summary (regenerated locally/CI) |
| `disagreements/*.json` | Retained semantic disagreements |

`manifest.json` may be gitignored or committed as a smoke snapshot; CI always
regenerates it. Committed disagreement files are intentional evidence of open
backend conflicts — do not delete to “make CI green.”
