# Mathematica adapter (wolframscript live path)

Closed v0 backend for `algebra.rational_equality` (RFC 0001),
`algebra.linear_algebra`, `logic.finite_counterexample`, live
`algebra.formal_rational_calculus` derivative/antiderivative candidates, and
`algebra.groebner_membership` (PolynomialReduce → sparse multipliers when
`MATHEVIDENCE_WOLFRAMSCRIPT` is set; otherwise fixture/`backend_unavailable`,
not advertised as live in the registry). Evidence contracts match the SymPy
adapter — never a trusted Boolean. Candidate calculus results never imply
completeness or uniqueness.

## Modes

| Mode | When | Behavior |
| --- | --- | --- |
| `fixture` | Default when `MATHEVIDENCE_WOLFRAMSCRIPT` is unset, or `MATHEVIDENCE_ADAPTER_MODE=fixture` | JSON-RPC works; `compute` returns `backend_unavailable` |
| `live` | `MATHEVIDENCE_WOLFRAMSCRIPT` set to an existing `wolframscript` executable | Spawns fixed-argv subprocess; RationalExpr + MatrixExpr + calculus ToIR |

Committed evidence under `evidence/` must always replay offline without
Mathematica. Public CI uses fixture / replay paths.

**Supported live transport:** `wolframscript` via
`MATHEVIDENCE_WOLFRAMSCRIPT`. LeanLink is not enabled for theorem acceptance.

## Environment

| Variable | Purpose |
| --- | --- |
| `MATHEVIDENCE_WOLFRAMSCRIPT` | Absolute path to `wolframscript` (**required** for live) |
| `MATHEVIDENCE_LEANLINK` | Path to LeanLink install (scaffold; unused for theorem acceptance) |
| `MATHEVIDENCE_ADAPTER_MODE` | `fixture` or `live` |

## Run

```text
# Fixture / CI
python -m adapters.mathematica

# Live (licensed host)
set MATHEVIDENCE_WOLFRAMSCRIPT=C:\Path\To\wolframscript.exe
python -m adapters.mathematica

# Or via CLI
set MATHEVIDENCE_WOLFRAMSCRIPT=C:\Path\To\wolframscript.exe
python scripts/mathevidence_cli.py compute --backend mathematica --request path/to/request.json --bundle-dir evidence/tmp/mm
```

JSON-RPC is newline-delimited JSON over stdio (same as SymPy).

## Live generator (RFC 0001 fragment)

When live, the rational adapter:

1. Encodes request `RationalExpr` IR as Wolfram InputForm (`+ − * / ^`, rationals, vars).
2. Runs `Together[Cancel[lhs - rhs]]`, extracts numerator / denominator factors.
3. Maps the result back to RationalExpr IR inside Wolfram (`ToIR`) — including
   non-zero numerators (false identities), not only the zero scaffold.
4. Emits the same certificate schema as SymPy
   (`schemas/rational-equality-certificate.schema.json`).

## Live linear algebra

When live, Inverse / LinearSolve / NullSpace / det_identity requests:

1. Encode `MatrixExpr` rationals as Wolfram matrices.
2. Run the corresponding exact solver over rationals.
3. Map results to MatrixExpr / ratLit IR matching SymPy certificates.
4. Lean `LinearAlgebra` checker owns acceptance.

## Live finite counterexample

When live, bounded domain enumeration (same algorithm as SymPy) is gated by
wolframscript live mode for honesty with other Mathematica ops. Lean
`Counterexample` checker owns acceptance.

## Live symbolic calculus (M5 polish)

When live, derivative/antiderivative requests:

1. Reuse the same RationalExpr encode + `ToIR` preamble as R1a.
2. Run `D[expr, x]` or `Integrate[expr, x]`, simplify/together, map to IR.
3. Rebind `requestDigest` with the generated candidate and emit
   `schemas/symbolic-calculus-certificate.schema.json`.
4. ODE/recurrence live path echoes request fields for Lean identity checks only
   (no uniqueness/completeness claim).

Registry support level is `live_generator_complete` for rational, LA, CEX, and
calculus code paths. Public CI without Wolfram still runs fixture / offline replay.

## LeanLink scaffold

LeanLink / LibraryLink remains **outside** the theorem TCB
(`docs/architecture/leanlink-adapter-review.md`). This package:

1. Discovers LeanLink via `MATHEVIDENCE_LEANLINK` and reports it on `initialize`.
2. Uses `wolframscript -code <script>` with an allow-listed environment.
3. Does **not** load native LeanLink bridges in CI.
4. Does **not** use LeanLink for certificate acceptance.

## Offline evidence

Generate with SymPy (or live Mathematica on a licensed machine), commit the
bundle under `evidence/examples/` or `evidence/conformance/`, then verify with:

```text
python scripts/offline_replay_python.py
```

Replay never starts Mathematica.

## Differential testing

```text
python scripts/run_differential_backends.py
```

When Wolfram is absent, Mathematica rows are labeled `fixture` / `skip` and
disagreements are never auto-resolved. Suites: rfc0001, linear_algebra accept,
finite_counterexample accept.
