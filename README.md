<p align="center">
```text
           __  __       _   _     _____       _     _
          |  \/  | __ _| |_| |__ | ____|_   _(_) __| | ___ _ __   ___ ___
          | |\/| |/ _` | __| '_ \|  _| \ \ / / |/ _` |/ _ \ '_ \ / __/ _ \
          | |  | | (_| | |_| | | | |___ \ V /| | (_| |  __/ | | | (_|  __/
          |_|  |_|\__,_|\__|_| |_|_____| \_/ |_|\__,_|\___|_| |_|\___\___|
```
  
<strong>External computation in. Lean theorems out.</strong>
</p>

<p align="center">
  <a href="docs/STATUS.md"><img src="https://img.shields.io/badge/status-experimental-orange" alt="Experimental" /></a>
  <a href="https://leanprover.github.io/"><img src="https://img.shields.io/badge/Lean-4-purple" alt="Lean 4" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="Apache 2.0" /></a>
</p>

MathEvidence turns results from external solvers into **Lean-checked evidence**:
adapters propose; Lean decides. SymPy and Mathematica adapters, an Agent API,
and Studio surfaces share one idea — use powerful external tools without
trusting them inside the theorem prover.

**Experimental** research preview: no capability is stable. See
[known limitations](docs/security/KNOWN_TRUST_GAPS.md) before relying on results.

## Why it exists

Formal work often needs exact algebra, search, or symbolic computation that
mature external systems already do well. One-off bridges reinvent translation
and trust boundaries — and can smuggle unchecked solver answers into proofs.

MathEvidence offers a shared path: an explicit semantic contract, checkable
evidence, and a reusable Lean theorem.

**Do not trust the solver. Lean checks the evidence.**

## Quick start

**Needs:** Lean matching [`lean-toolchain`](lean-toolchain), Python 3 with the
repo requirements, and [`just`](https://github.com/casey/just).

```text
git clone https://github.com/fraware/MathEvidence.git
cd MathEvidence
just check
```

That runs the local build and test gate. Full walkthrough:
[`docs/getting-started/`](docs/getting-started/).

Optional: SymPy for open backends; `wolframscript` (set
`MATHEVIDENCE_WOLFRAMSCRIPT`) for live Mathematica. Bundles under `evidence/`
replay offline without a live CAS.

## Try one example

Open the committed rational-equality example
`(x^2 - 1)/(x - 1) = x + 1` (with an explicit denominator condition):

```text
evidence/examples/rational_equality_basic/
```

Inspect `request.cjson`, `certificate.cjson`, and `theorem.lean`. Lean owns
acceptance; the adapter is untrusted. Then follow
[`docs/getting-started/`](docs/getting-started/) for offline replay, or start
the local Agent API:

```text
python -m agent.api.server --host 127.0.0.1 --port 8787
```

Health check: `GET http://127.0.0.1:8787/v1/health`. Public open / inspect /
replay take opaque `bundleId` values — not filesystem paths. See
[`agent/README.md`](agent/README.md).

## Repository map

| Path | Role |
| --- | --- |
| `MathEvidence/` | Lean protocol types, encodings, checkers, tactics |
| `adapters/` | Untrusted backends (SymPy, Mathematica, and related) |
| `agent/` | AI-facing Agent API and SDKs |
| `studio/` | Notebook and editor surfaces |
| `registry/` | Capability declarations (all experimental today) |
| `evidence/` | Committed Evidence Bundles (schema v0.2 `.cjson`) |
| `foundry/` | Schemas and pipelines for certified tool-use episodes |
| `benchmarks/` | Conformance, adversarial, and real-world suites |
| `docs/` | Specs, status, trust model, getting started |

## Contribute

Contributions are welcome. Keep backends untrusted and Lean authoritative.

1. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/STATUS.md`](docs/STATUS.md).
2. Prefer a focused change with tests (positive, negative, and replay when relevant).
3. Run `just check` before opening a PR.
4. Do not flip capabilities to `"stable"` from a single PR — promotion follows a
   documented checklist with real human review.

Protocol-wide changes belong in an RFC under `docs/rfcs/`.

## Documentation

| Doc | Purpose |
| --- | --- |
| [`docs/README.md`](docs/README.md) | Documentation landing |
| [`docs/getting-started/`](docs/getting-started/) | Install, check, Agent API, first replay |
| [`docs/STATUS.md`](docs/STATUS.md) | Public-preview status |
| [`docs/security/KNOWN_TRUST_GAPS.md`](docs/security/KNOWN_TRUST_GAPS.md) | Known limitations |

Also: [`docs/SPEC_INDEX.md`](docs/SPEC_INDEX.md),
[`docs/ROADMAP.md`](docs/ROADMAP.md),
[`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md).

## What to expect

- Everything in the registry is still **experimental**.
- A green local `just check` is useful feedback — not attested release CI or
  completed human review.
- Receipt crypto under `dev/receipt-keys/` is **dev-only**, not production PKI.

When unsure, trust Lean’s checkers and the written limitations — not a backend
status code.

---

**License** [`LICENSE`](LICENSE) (Apache-2.0) ·
**Security** [`SECURITY.md`](SECURITY.md) ·
**Contributing** [`CONTRIBUTING.md`](CONTRIBUTING.md)
