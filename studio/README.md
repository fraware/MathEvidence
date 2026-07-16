# Studio

Human-facing clients. **No unique mathematical semantics** — Studio is a client
of Lean checkers, IR schemas, the capability registry, and the Agent API.

## Surfaces

| Path | Status |
| --- | --- |
| `vscode/` | Evidence inspector (Computed / Tested / Certified / Ambiguous) |
| `wolfram/` | Wolfram Studio epistemic workflow |
| `epistemic_contract.py` | Shared Python reference for Certified gate + surface order |
| `golden/` | Integration golden transcripts (not human usability) |

See `studio/vscode/README.md` and `studio/wolfram/README.md`.

## Hard rules (Product 09)

1. **Certified** only when Lean status is present (and exact Lean proposition text is available on the certification surface).
2. Lean proposition + assumptions are always shown **before** the Certified affordance.
3. Manifest-only “verified” without Lean → **Ambiguous**.

## Tests

```text
python -m pytest adapters/common/test_epistemic_studio.py -q
just studio-test
```

Usability (human): `docs/validation/studio/usability/` — session results remain OPEN.
