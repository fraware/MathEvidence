# Discovery orchestration

## Modes

| Mode | Gate | Behavior |
| --- | --- | --- |
| Offline (default) | `MATHEVIDENCE_DISCOVERY` unset | Meta-reify ℚ equality; match committed fixtures; **never** spawn adapters |
| Live | `MATHEVIDENCE_DISCOVERY=1`/`true`/`live` | Spawn `scripts/mathevidence_cli.py discover` → adapter compute → Lean check |

Public CI must keep the offline default.

## Python CLI

```text
# In-process SymPy (CI-safe)
python scripts/mathevidence_cli.py discover --backend sympy --request path/to/request.json --bundle-dir out/ --direct

# JSON-RPC subprocess (also set MATHEVIDENCE_DISCOVERY_RPC=1)
python scripts/mathevidence_cli.py discover --backend sympy --request path/to/request.json --rpc --emit-certificate
```

Mathematica/Sage live compute still requires their env gates
(`MATHEVIDENCE_WOLFRAMSCRIPT` / `MATHEVIDENCE_SAGE`); otherwise fixture mode
returns `backend_unavailable`.

## Lean tactic

```lean
example (x : ℚ) (hx : x - 1 ≠ 0) :
    (x ^ 2 - 1) / (x - 1) = x + 1 := by
  mathevidence
```

- Reifies the goal into `RationalExpr`
- Matches `evidence/examples/rational_equality_basic` offline
- Closes with `field_simp; ring` when denominator hypotheses are present

## Trust

Adapters remain outside the TCB. Lean re-checks certificates with
`RationalEquality.checkBool` before any close attempt.
