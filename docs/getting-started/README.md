# Getting started

Install the monorepo toolchain, run the local engineering gate, and exercise
offline replay / the Agent API. MathEvidence remains **experimental** — read
[`../STATUS.md`](../STATUS.md) and
[`../security/KNOWN_TRUST_GAPS.md`](../security/KNOWN_TRUST_GAPS.md) before
relying on any capability.

## Prerequisites

- Lean toolchain matching the committed `lean-toolchain`
- Python 3 with the repo requirements files (`requirements.txt` /
  `requirements-dev.txt`, or the project’s uv/`pyproject.toml` workflow)
- [`just`](https://github.com/casey/just)

Optional:

- SymPy (open reference backend; used by several conformance paths)
- `wolframscript` when exercising live Mathematica adapters
  (`MATHEVIDENCE_WOLFRAMSCRIPT`)

## Clone and check

```text
git clone https://github.com/fraware/MathEvidence.git
cd MathEvidence
just check
```

`just check` runs the local engineering gate: Lean build, audits,
schema/registry validation, Python tests, conformance, replay, and related
harnesses.

### Windows: kernel-replay rsp (required)

On Windows with Lean **v4.14**, bare `lake build mathevidence-kernel-replay`
often fails to link (CreateProcess error 206 / command line too long). The
**required** local path is the response-file helper:

```text
python scripts/link_exe_via_rsp.py mathevidence-kernel-replay
just exe-smoke
```

`just exe-smoke` / `scripts/smoke_exe.py` attempt rsp automatically and, if
linking still fails, degrade with `replay_dependency_missing` (never fake
Certified). **Linux CI** (`.github/workflows/lean.yml`) remains the
authoritative linked-exe attestation (`--self-test` + `--self-test-analytic`).
Details: [`../audits/2026-07-26-real-vision/KERNEL_REPLAY_PLATFORM.md`](../audits/2026-07-26-real-vision/KERNEL_REPLAY_PLATFORM.md).

Focused trust subset:

```text
pytest tests/forensic -q
```

**CI honesty:** workflow definitions live under `.github/workflows/`. A green
local `just check` is not promotion evidence and is not an attested immutable
CI green on a release commit.

## First offline replay

Committed Evidence Bundle trees under `evidence/` use schema **v0.2** (`.cjson`)
for full bundles. Prefer replaying through the documented CLI /
`mathevidence-verify-bundle` (temporary alias `mathevidence-replay`) for
rational equality emits operational `native_checked` / `checker_accepted`
only — not theorem Certified / `kernel_replay`.
or through the Agent API below.

Do not treat backend status codes as theorems. Replay must recheck committed
evidence without trusting the solver.

## Agent API (local)

```text
python -m agent.api.server --host 127.0.0.1 --port 8787
```

Health: `GET http://127.0.0.1:8787/v1/health`

Public open / inspect / replay accept opaque **`bundleId`** values from the
content-addressed store only — raw filesystem paths are rejected. See
[`../../agent/README.md`](../../agent/README.md).

## Formal rational calculus

Registry id: `algebra.formal_rational_calculus` (formal rational-expression
calculus only). It does not establish Mathlib `HasDerivAt` / analytic ODE
theorems. Analytic fragments use the separate experimental id
`analysis.analytic_calculus`.

## Next reading

| Doc | Why |
| --- | --- |
| [`../HANDOFF.md`](../HANDOFF.md) | Exact-certification engineering handoff / runbook |
| [`../STATUS.md`](../STATUS.md) | Preview claims and non-claims |
| [`../security/KNOWN_TRUST_GAPS.md`](../security/KNOWN_TRUST_GAPS.md) | Trust gaps |
| [`../products/README.md`](../products/README.md) | Product surface map |
| [`../architecture/README.md`](../architecture/README.md) | Architecture notes |
| [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) | Contribution rules |
