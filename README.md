<div align="center">

<pre>
  
           __  __       _   _     _____       _     _
          |  \/  | __ _| |_| |__ | ____|_   _(_) __| | ___ _ __   ___ ___
          | |\/| |/ _` | __| '_ \|  _| \ \ / / |/ _` |/ _ \ '_ \ / __/ _ \
          | |  | | (_| | |_| | | | |___ \ V /| | (_| |  __/ | | | (_|  __/
          |_|  |_|\__,_|\__|_| |_|_____| \_/ |_|\__,_|\___|_| |_|\___\___|

</pre>
  
<strong>External computation in. Explicit evidence. Lean decides.</strong>
</div>

<p align="center">
  <a href="docs/STATUS.md"><img src="https://img.shields.io/badge/status-experimental-orange" alt="Experimental" /></a>
  <a href="https://leanprover.github.io/"><img src="https://img.shields.io/badge/Lean-4-purple" alt="Lean 4" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="Apache 2.0" /></a>
</p>

MathEvidence turns results from external solvers into **Lean-checked evidence**:
adapters propose; Lean decides. SymPy and Mathematica adapters, an Agent API,
and Studio surfaces share one idea — use powerful external tools without
trusting them inside the theorem prover.

**Experimental** research preview: no capability is stable. Theorem-level
Certification Records require exact candidate binding **and current registry CR
eligibility** ([ADR 0005](docs/adr/0005-exact-candidate-binding.md)); see
[status](docs/STATUS.md) and
[known limitations](docs/security/KNOWN_TRUST_GAPS.md) before relying on results.

## Why it exists

Formal work often needs exact algebra, search, or symbolic computation that
mature external systems already do well. One-off bridges reinvent translation
and trust boundaries — and can smuggle unchecked solver answers into proofs.

MathEvidence offers a shared path: explicit semantic contracts, candidate-bound
evidence, capability-specific checkers, and reproducible verification.

**Do not trust the solver. Trust only the proposition the declared checker
actually establishes.**

## Current exact scope

The registry currently marks five owned capability fragments CR-eligible under
exact candidate binding. These are narrow contracts, not generic automation
claims. Rational equality remains an experimental checker/soundness/bridge
capability but is deliberately fail-closed for theorem Certification Records in
the pinned Lean 4.14 public-preview path.

| Capability | Exact claim scope |
| --- | --- |
| `algebra.ideal_membership_witness` | Supplied witness establishes the supported polynomial ideal-membership identity; no Gröbner/non-membership/completeness claim |
| `algebra.linear_algebra` | Exact rational `inverse_witness`, `system_solution`, `kernel_vector`, and `det_identity` operations |
| `logic.finite_counterexample` | Explicit finite witness establishes `refuted`; no-witness search does not prove universality |
| `algebra.formal_rational_calculus` | Registered formal/algebraic grammar and exact `soundResult` operations only |
| `analysis.analytic_calculus` | Strict registered theorem-form whitelist with explicit hypotheses; not arbitrary analysis |

`algebra.rational_equality` still exposes its exact rational-expression checker,
soundness theorem, bridge, and generator surface. Theorem-CR promotion is
disabled for this release because the candidate-specific checker proposition
cannot be admitted on the production Lean 4.14 native-reduction path without an
unacceptable `sorryAx` dependency. Fixture closure is not substituted for that
missing candidate theorem.

Federated SAT/PB/SMT metadata is not theorem-CR eligible in this repository.
The authoritative machine-readable state is
[`registry/maturity-inventory.json`](registry/maturity-inventory.json).

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

**Windows kernel-replay:** Lean 4.14 Lake may fail to link
`mathevidence-kernel-replay` (CreateProcess 206). The **required** local path
is `python scripts/link_exe_via_rsp.py mathevidence-kernel-replay` (also
attempted by `just exe-smoke` / `scripts/smoke_exe.py`). Linux CI remains
authoritative — see
[`docs/audits/2026-07-26-real-vision/KERNEL_REPLAY_PLATFORM.md`](docs/audits/2026-07-26-real-vision/KERNEL_REPLAY_PLATFORM.md).

Optional: SymPy for open backends; `wolframscript` (set
`MATHEVIDENCE_WOLFRAMSCRIPT`) for live Mathematica. Sealed exact replay bundles
can be regenerated and integrity-checked without a live CAS after dependencies
are materialized. This **offline bundle replay** is distinct from a required
offline Lean/kernel theorem-execution guarantee; see
[`docs/STATUS.md`](docs/STATUS.md).

## Try one example

Open the committed rational-equality example
`(x^2 - 1)/(x - 1) = x + 1` (with an explicit denominator condition):

```text
evidence/examples/rational_equality_basic/
```

Inspect `request.cjson`, `certificate.cjson`, and `theorem.lean`. The adapter is
untrusted. Checker/theorem authority is determined by the declared assurance
path, not by the presence of those files alone. In the pinned Lean 4.14 public
preview this capability is **not** theorem-CR eligible; the committed theorem is
therefore not release authority for an arbitrary submitted candidate. Then
follow [`docs/getting-started/`](docs/getting-started/) for replay, or start the
local Agent API:

```text
python -m agent.api.server --host 127.0.0.1 --port 8787
```

Health check: `GET http://127.0.0.1:8787/v1/health`. Public open / inspect /
replay take opaque `bundleId` values — not filesystem paths. See
[`agent/README.md`](agent/README.md).

## Assurance chain

For an exact CR-eligible path, the intended chain is:

```text
submitted request + candidate/evidence
  -> schema/canonical validation
  -> capability-specific exact replay IR
  -> deterministic generated Lean source
  -> pinned Lean/checker execution
  -> declaration/result identity
  -> registry policy evaluation
  -> Certification Record
```

Generation is not verification. Fixture replay is not candidate verification.
Benchmark success is not theorem promotion. Unsupported exact modes fail closed.
The required `lean` CI workflow executes production-generated exact candidates
for every CR-eligible capability; structural generator tests alone do not
satisfy that release gate.

## Repository map

| Path | Role |
| --- | --- |
| `MathEvidence/` | Lean protocol types, encodings, checkers, tactics |
| `adapters/` | Untrusted backends and exact replay generation framework |
| `agent/` | AI-facing Agent API and SDKs |
| `studio/` | Notebook and editor surfaces |
| `registry/` | Capability declarations and machine-readable assurance maturity |
| `evidence/` | Committed Evidence Bundles and conformance artifacts |
| `foundry/` | Schemas and pipelines for verified tool-use episodes |
| `benchmarks/` | Frozen conformance/regression and evaluation suites |
| `docs/` | Specs, status, trust model, getting started, release docs |

## Contribute

Contributions are welcome. Keep backends untrusted and checker authority
explicit.

1. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/STATUS.md`](docs/STATUS.md).
2. Prefer a focused change with positive, negative, mutation, and replay tests
   where relevant.
3. Run `just check` before opening a PR.
4. Exact-capability changes must preserve candidate binding and fail-closed
   policy; never substitute a fixture for the submitted candidate.
5. Do not flip capabilities to `"stable"` from a single PR — promotion follows
   the documented checklist with real human/domain/trust review.

Protocol-wide changes belong in an RFC under `docs/rfcs/`.

## Documentation

| Doc | Purpose |
| --- | --- |
| [`docs/README.md`](docs/README.md) | Documentation landing |
| [`docs/getting-started/`](docs/getting-started/) | Install, check, Agent API, first replay |
| [`docs/STATUS.md`](docs/STATUS.md) | Public-preview status and CR eligibility |
| [`docs/HANDOFF.md`](docs/HANDOFF.md) | Exact-certification operator runbook |
| [`docs/security/KNOWN_TRUST_GAPS.md`](docs/security/KNOWN_TRUST_GAPS.md) | Known limitations and trust gaps |

Also: [`docs/SPEC_INDEX.md`](docs/SPEC_INDEX.md),
[`docs/ROADMAP.md`](docs/ROADMAP.md),
[`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md).

## What to expect

- Everything in the registry is still **experimental**.
- Five owned capability fragments are CR-eligible under exact candidate binding;
  rational equality and federated logic are not theorem-CR eligible in this
  release.
- Offline **bundle** replay and offline **kernel** theorem replay are tracked as
  distinct maturity properties; the stronger kernel property is not currently
  claimed release-wide.
- A green local `just check` is useful feedback — not attested release CI or
  completed human review.
- The final release SHA must have the required remote assurance/security/replay
  gates green. Repository branch/ruleset configuration is operational governance,
  not mathematical assurance evidence for this experimental preview.
- Receipt crypto under `dev/receipt-keys/` is **dev-only**, not production PKI.
  Production signing / third-party attestation remains a separate explicit gate.

When unsure, follow the exact proposition, checker, registry policy, and current
limitations — not a backend status code or historical completion label.

---

**License** [`LICENSE`](LICENSE) (Apache-2.0) ·
**Security** [`SECURITY.md`](SECURITY.md) ·
**Contributing** [`CONTRIBUTING.md`](CONTRIBUTING.md)
