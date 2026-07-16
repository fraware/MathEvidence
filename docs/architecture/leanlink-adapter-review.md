# LeanLink Adapter Design Review (Phase 0)

Review target: Mathematica adapter via LeanLink (`adapters/mathematica`), per
`docs/SECURITY_AND_TRUST_MODEL.md` §7 and ADR 0003 (JSON-RPC over stdio).

## Goals

- Map MathEvidence requests to Wolfram Language exactly for supported IR.
- Emit solver-independent candidates and evidence (never a trusted Boolean).
- Keep LeanLink / LibraryLink / C bridge **outside** theorem acceptance.
- Preserve offline replay: committed Mathematica evidence must check without
  Mathematica in public CI.

## Trust boundary

```text
Lean tactic / orchestrator
        |  JSON-RPC stdio (versioned request)
        v
adapters/mathematica (untrusted)
        |  LeanLink / WXF / LibraryLink
        v
Mathematica kernel (untrusted)
        |  candidate + provenance + provenance
        v
Lean checker (trusted path)
```

Invariant: a compromised or buggy LeanLink path can waste resources or emit
garbage evidence; it must not create Lean declarations in a trusted environment.

## Process isolation checklist

- [ ] Fixed executable paths; no shell interpolation or `cmd.exe` composition.
- [ ] Explicit CPU, wall-time, memory, and output-size limits.
- [ ] Isolated working directory; generated paths normalized under workspace.
- [ ] Environment allow-list only; credentials never written into evidence.
- [ ] Network denied unless a future capability explicitly documents need.
- [ ] Cancel / shutdown mapped to kernel kill with bounded cleanup.

## C-bridge / native risk checklist

- [ ] Memory-safety review of LeanLink native components used by the adapter.
- [ ] Malformed WXF / binary fuzz corpus under `security.yml` expansion.
- [ ] Handle-lifetime tests (no use-after-free across RPC calls).
- [ ] Cross-platform conformance (Windows primary for MathEvidence bootstrap;
      Linux CI for open path).
- [ ] Toolchain pin compatibility matrix (Lean ↔ LeanLink ↔ Mathematica).

## JSON-RPC mapping (planned)

| Method | Mathematica adapter behavior |
| --- | --- |
| `initialize` | Report adapter + LeanLink + Mathematica versions; capability list |
| `listCapabilities` | Declare `algebra.rational_equality` support flags |
| `checkSupport` | Reject unsupported syntax without kernel call when possible |
| `compute` | Translate IR → WL, run exact ops, return candidate + conditions |
| `cancel` | Interrupt kernel evaluation |
| `shutdown` | Tear down session |

Errors use Project Spec stable codes (semantic / backend / evidence / system).

## Design decisions locked for Phase 1

1. Same evidence contract as SymPy for rational equality (RFC 0001).
2. Discovery may be self-hosted / optional in CI; replay is mandatory publicly.
3. Paclet layered on LeanLink; no unique Studio semantics inside the adapter.

## Open items (track into Phase 1G / 1H)

- Exact LeanLink API surface and packaging (paclet vs Python supervisor).
- WXF vs JSON for large certificates (binary only with versioned Lean decoder).
- License / redistribution review before Foundry publication of WL artifacts.
- Native bridge remains **disabled** (`adapters/mathematica/leanlink.py`);
  `initialize` reports LeanLink path when `MATHEVIDENCE_LEANLINK` is set.
- Live IR decode currently accepts zero-numerator identities only; richer
  WL→RationalExpr mapping awaits the paclet.

## Sign-off

Phase 0 produces this review artifact. Implementation and fuzz harnesses are
Phase 1; this document is the acceptance checklist for that work.

**No maintainer sign-off is claimed here.** Track execution below.

## Execution notes (engineering status — not sign-off)

| Checklist item | Status | Notes |
| --- | --- | --- |
| Fixed executable paths; no shell interpolation | **met** | `adapters/mathematica/adapter.py` uses argv lists |
| CPU / wall / memory / output limits | **partial** | wall + output via `ResourceLimits`; OS memory caps not enforced |
| Isolated working directory | **partial** | cwd pinned to repo root for supervisor; no sandbox FS |
| Environment allow-list | **met** | only `MATHEVIDENCE_*` + PATH subset forwarded |
| Network denied | **met (default)** | adapter does not open sockets |
| Cancel / shutdown → kernel kill | **partial** | process terminate on client close; richer cancel TBD |
| Native LeanLink bridge disabled in CI | **met** | `leanlink.py` scaffold; `MATHEVIDENCE_LEANLINK` reported only |
| Live IR decode narrow | **met** | fixture mode default; live zero-numerator scaffold |
| Public CI without Mathematica | **met** | fixture + committed offline evidence |
| Fuzz corpus under `security.yml` | **open** | expand when LeanLink paclet lands |

### Operator live path

```text
set MATHEVIDENCE_ADAPTER_MODE=live
set MATHEVIDENCE_WOLFRAMSCRIPT=C:\Path\To\wolframscript.exe
python -m adapters.mathematica
```

Discovery from Lean still requires `MATHEVIDENCE_DISCOVERY=1` and will not run
in public CI.
