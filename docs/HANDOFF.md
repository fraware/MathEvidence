# MathEvidence engineering handoff

Operator and onboarding runbook for the exact-candidate-binding program
(SPEC-12). Use this document with repository-local specs alone; do not rely on
PR discussion or maintainer memory for assurance semantics.

**Related authority**

| Doc | Role |
| --- | --- |
| [`adr/0005-exact-candidate-binding.md`](adr/0005-exact-candidate-binding.md) | Non-negotiable invariant |
| [`validation/handoff-2026-08-25-delta.md`](validation/handoff-2026-08-25-delta.md) | SPEC-00 pin / CI delta |
| [`../MathEvidence_Engineering_Handoff_2026-08-25/`](../MathEvidence_Engineering_Handoff_2026-08-25/) | Engineering handoff package (specs, architecture, acceptance) |
| [`../MathEvidence_Engineering_Handoff_2026-08-25/03_ACCEPTANCE_MATRIX.md`](../MathEvidence_Engineering_Handoff_2026-08-25/03_ACCEPTANCE_MATRIX.md) | Program exit acceptance matrix |
| [`../registry/maturity-inventory.json`](../registry/maturity-inventory.json) | Machine-readable maturity / `cr_eligible` |
| [`STATUS.md`](STATUS.md) | Short public-preview status (registry-backed table) |

---

## 1. Purpose and assurance invariant

MathEvidence is an **experimental** computational-evidence platform for Lean:
protocol, semantic IR, verified checkers, untrusted adapters, Agent API, Studio
surfaces, registry, Foundry samples, and offline evidence bundles.

**Non-negotiable invariant (ADR 0005):** a theorem-level Certification Record
may be issued only when the **exact submitted candidate** was verified by the
declared trusted path.

Consequences that must never be weakened in docs or code:

- Fixture / nearby theorems do not certify a different submitted candidate.
- Exact mode never silently downgrades to fixture or bridge replay.
- Floats never coerce into exact rational/integer certificates.
- Generated Lean for exact replay comes from typed ReplayIR only.
- Checker pass, OfflineFixtures, benchmarks, and numerical agreement never
  authorize Certification Record promotion by themselves.

---

## 2. Current baseline

| Item | Value |
| --- | --- |
| Upstream integration PR | [#53](https://github.com/fraware/MathEvidence/pull/53) (`fix/exact-certification-binding`) |
| Handoff / program pin | `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b` |
| Working branch | `phase4/exact-certification-handoff` (from `phase3/exact-certification-release`; do **not** rebase onto `main`) |
| HEAD commit | `30522d70` (pin); Phases 0-4 program work is largely **uncommitted** on this branch |
| Current `main` | Still fixture-substitution semantics — **not** this program's baseline |

Phases 0-3 landed as working-tree changes on the pin (registry/assurance policy,
typed exact_replay framework, CR v0.4, capability generators, offline bundle,
CI dimension split, security adversarial coverage). Phase 4 is this runbook.

Do **not** claim theorem CR eligibility for capabilities that still have
`crEligible=false`. Currently eligible after local Lean exact-replay E2E:
ideal membership, rational equality, linear algebra (all four ops), finite
counterexample (`refuted`), formal rational calculus (derivative /
antiderivative / recurrence / ODE with `soundResult`), and analytic calculus
whitelist (Deriv / DerivWithin / Antideriv / ODE). Federated logic remains
blocked. Offline theorem inspect defaults to `theorem_pending`; set
`MATHEVIDENCE_OFFLINE_LEAN=1` or `require_lean=True` to attempt
`theorem_proved` when Lake is available.

---

## 3. Architecture and trust boundary

Adapted from the handoff package
[`01_TARGET_ARCHITECTURE.md`](../MathEvidence_Engineering_Handoff_2026-08-25/01_TARGET_ARCHITECTURE.md).

### End-to-end data flow

```text
Claim / Candidate / Evidence
          |
          v
[Canonical schema validation]
          |
          v
[Capability adapter + evidence checker]
          |
          +------------------------------+
          |                              |
          | lower assurance              | exact/theorem assurance requested
          v                              v
[Evidence result]              [Assurance capability registry]
                                         |
                              unsupported? -> FAIL CLOSED
                                         |
                                         v
                              [Typed exact replay IR]
                                         |
                                         v
                             [Deterministic Lean generator]
                                         |
                                         v
                               [Generated replay module]
                                         |
                                         v
                          [Pinned Lean/toolchain verification]
                                         |
                                         v
                              [Declaration/result identity]
                                         |
                                         v
                           [Certification policy evaluator]
                                         |
                                         v
                              [Certification Record]
                                         |
                                         v
                           [Offline replay bundle + audit]
```

### Trusted-computing boundary (theorem / exact mode)

Trusted for Lean-backed exact certification (when enabled):

- canonical input decoding/validation;
- semantics-preserving translation from typed candidate IR to generated Lean
  (`adapters/common/exact_replay/`);
- pinned Lean kernel/toolchain and declared dependencies
  (`lean-toolchain`, `lake-manifest.json`);
- the specific checker / theorem / declaration invoked
  (`mathevidence-declaration-identity`);
- Certification Record canonicalization and binding
  (`agent/api/receipt.py`, schemas).

Outside that path (adapters, solvers, benchmarks, Studio UX, OfflineFixtures
self-tests) can be useful evidence but does **not** authorize theorem-level
promotion.

### Capability maturity (derived, not marketing)

```text
REGISTERED
  -> CHECKER_AVAILABLE
  -> FORMALLY_SPECIFIED
  -> BRIDGE_REPLAY_AVAILABLE
  -> EXACT_REPLAY_AVAILABLE
  -> OFFLINE_REPLAY_VERIFIED
  -> CR_ELIGIBLE
```

Underlying booleans live in `registry/maturity-inventory.json` and each
capability's `assurancePolicy.maturity`. `CR_ELIGIBLE` is a registry policy bit
(`assurancePolicy.certification.crEligible`), never a hand-edited status claim.

---

## 4. Setup

Prerequisites and clone steps: [`getting-started/README.md`](getting-started/README.md).

Summary:

1. Toolchain matching committed `lean-toolchain` (expect Lean **v4.14.0**).
2. Python 3 + `uv` (`uv sync --frozen --extra dev --extra sympy`).
3. [`just`](https://github.com/casey/just).
4. Optional: SymPy (default open backend); `MATHEVIDENCE_WOLFRAMSCRIPT` for live
   Mathematica; Sage on `PATH` for live Sage.

Windows kernel-replay link: use `python scripts/link_exe_via_rsp.py
mathevidence-kernel-replay` (see getting-started). Never fake Certified on link
failure.

Work from the exact-certification branch / pin — **not** current `main`.

---

## 5. Local verification commands

Run from repository root. Prefer `uv run` / activated `.venv` when needed.

### Registry and maturity (CR honesty)

```text
python scripts/validate_registry.py
python scripts/validate_maturity_inventory.py
just registry-validate
```

`validate_maturity_inventory.py` checks inventory consistency and that
`docs/STATUS.md` does not claim CR eligibility the registry denies.

### Schemas / assurance contracts

```text
python scripts/validate_schemas.py
python scripts/validate_assurance.py
just schema-validate
just assurance-validate
```

### Forensic subsets (exact binding / policy / CR v0.4 / security)

```text
just forensic-test
# or focused:
python -m pytest tests/forensic/test_assurance_policy.py -q
python -m pytest tests/forensic/test_exact_candidate_binding.py -q
python -m pytest tests/forensic/test_exact_replay_framework.py -q
python -m pytest tests/forensic/test_exact_phase2_plugins.py -q
python -m pytest tests/forensic/test_certification_record_v04.py -q
python -m pytest tests/forensic/test_assurance_adversarial_corpus.py -q
python -m pytest tests/forensic/test_exact_replay_security.py -q
python -m pytest tests/forensic/test_maturity_inventory.py -q
```

### Lake / Lean targets (theorem path)

```text
lake build
lake build mathevidence-verify-bundle
lake build mathevidence-declaration-identity
lake build mathevidence-axiom-report
lake build MathEvidence.Checkers.IdealMembership.OfflineFixtures
```

Local Lean exact-replay E2E is green for all six owned exact-bound capabilities
after fixing:

1. generated olean output under `.lake/build/lib/` (never `.lake/build/lib/lean/`,
   which shadows toolchain `Lean` on case-insensitive Windows);
2. `lake exe mathevidence-declaration-identity` argv without a bare `--`
   separator (Lake 5 forwards `--` into the exe and DeclarationIdentity exits 2);
3. generators emitting named `def` claim/req/cert so
   `Claim.proposition req.claim` unifies with `replaySound` (and analytic
   Soundness decls).

Do not treat a partial Lake success as blanket enablement for federated or
non-registered capabilities. Flip `crEligible` only after that capability's own
compile/identity ladder is green.

### Offline exact replay + tamper (SPEC-09; structure / regenerability)

```text
just replay-exact-offline
# equivalent:
python -m pytest tests/forensic/test_offline_exact_replay.py -q
python scripts/offline_exact_replay.py tamper-selftest

# build / replay a bundle directory:
python scripts/offline_exact_replay.py build --out /tmp/exact-bundle
python scripts/offline_exact_replay.py replay --bundle /tmp/exact-bundle --both-modes
```

Offline driver modes: `regenerate-and-verify` and `artifact-replay`. Default
logical outcome is `theorem_pending` (integrity only). With
`MATHEVIDENCE_OFFLINE_LEAN=1` or `require_lean=True` and Lake available,
inspect can yield `theorem_proved`; setup/missing Lake stays distinct from
`theorem_failure`.

### Full local engineering gate

```text
just check
```

Local green is not promotion evidence and is not attested immutable CI green.

---

## 6. CI gate map (Phase 3 split)

Normative workflow notes: [`.github/workflows/README.md`](../.github/workflows/README.md),
[`TESTING_AND_CI.md`](TESTING_AND_CI.md).

| Dimension / job | Workflow | What it proves | What it does **not** prove |
| --- | --- | --- | --- |
| `assurance-exact-replay` | `assurance-exact-replay.yml` | Registry/maturity gates; exact regenerability forensics (no Lake theorem mint) | CR eligibility; Lean kernel theorem |
| `replay-tamper` | `replay-tamper.yml` | Offline bundle tamper matrix fails closed | Lean-proved offline success |
| `offline-replay` | `offline-replay.yml` | Python exact bundle + Lean fixture / OfflineFixtures leg | Theorem CR |
| `lean-assurance-audit` | `lean-assurance-audit.yml` | Python-side Lean assurance audits | Full `lake build` (that remains `lean.yml`) |
| `security-bounded-execution` | `security.yml` | Bounds, path confinement, adversarial exact-replay security | Mathematical soundness |
| `benchmark-task-suite` | `benchmarks.yml` | Python task / Foundry / held-out suites | Never writes `crEligible` |
| `ideal-release-grade` | `benchmarks.yml` | Ideal release-grade path (depends on Lake) | Setup/Lake failure is not benchmark logic failure |
| `adapter-conformance` | `adapter-conformance.yml` | Adapter contracts | Exact binding / CR |
| `supply-chain` | `supply-chain.yml` | Locks / vendor provenance | Assurance |
| `lean` | `lean.yml` | Lake build + declaration-identity + audits | Must stay honest when red (SPEC-01) |
| Also | `adversarial.yml`, `release.yml`, `uv-lock.yml` | Seeded adversarial / release / lock | CR promotion |

Triage: if `benchmark-task-suite` is green but `assurance-exact-replay` or
`lean` is red, do **not** narrate "assurance green."

---

## 7. Capability registry / `assurancePolicy` format

- Discovery catalog: [`registry/catalog.json`](../registry/catalog.json)
- Per-capability files: [`registry/capabilities/*.json`](../registry/capabilities/)
  (schema: [`schemas/capability.schema.json`](../schemas/capability.schema.json))
- Maturity inventory: [`registry/maturity-inventory.json`](../registry/maturity-inventory.json)
  (schema: [`schemas/maturity-inventory.schema.json`](../schemas/maturity-inventory.schema.json))
- Embedded policy schema: [`schemas/assurance-policy.schema.json`](../schemas/assurance-policy.schema.json)
- Loader: [`agent/api/assurance_policy.py`](../agent/api/assurance_policy.py)

`assurancePolicy` is the **only** authority for theorem promotion. Required
shape (conceptual):

```json
{
  "supportedAssuranceModes": ["kernel_replay"],
  "exactBinding": {
    "supported": true,
    "generatorId": "mathevidence.exact_ideal_membership",
    "generatorVersion": "0.1.0",
    "grammarVersion": "0.1.0",
    "generatorPath": "scripts/generate_exact_ideal_replay_module.py",
    "verifier": "mathevidence-declaration-identity"
  },
  "replay": { "backend": "exact_generator", "offlineSupported": true },
  "certification": { "allowedOutcomes": [], "crEligible": false },
  "maturity": {
    "adapterExists": true,
    "checkerExists": true,
    "leanSoundnessExists": true,
    "bridgeReplayExists": true,
    "exactCandidateBindingExists": true,
    "offlineReplayExists": true
  },
  "limitations": ["..."]
}
```

Policy rules enforced in code / validators:

1. Unknown capability => no CR
2. Unsupported mode => stable `assurance_mode_unavailable`
3. Exact requested + `exactBinding.supported=false` => fail closed
4. No exact to fixture/bridge fallback
5. Outcome must be in `allowedOutcomes`
6. Capability/version immutable in an issued record
7. Increasing assurance in the registry is a security-sensitive review

---

## 8. Certification Record lifecycle (v0.3 vs v0.4)

Schemas: [`schemas/certification-record.schema.json`](../schemas/certification-record.schema.json),
[`schemas/certification-receipt.schema.json`](../schemas/certification-receipt.schema.json).
Verifier: [`agent/api/receipt.py`](../agent/api/receipt.py).

| Version | Role |
| --- | --- |
| **v0.3** | Legacy. Parse under original `schemaVersion` / `bundleVersion` `0.3.0`. Fixture-backed or incomplete exact identity must map to **lower** assurance; never synthesize missing generator / grammar / source hashes. |
| **v0.4** | Current exact-promotion shape (`0.4.0`). Adds explicit `outcome` polarity (`proved` \| `refuted` \| `evidence_only`) alongside protocol `resultStatus`. Mandatory exact fields include claim/candidate hashes, `assuranceMode`, generator/grammar versions, generated source hash, declaration identity, toolchain/dependency lock digests, artifact hashes, replay manifest hash, execution policy id. |

Rules:

- Do not silently upgrade v0.3 records to v0.4.
- Do not overload `resultStatus` for polarity; use `outcome`.
- Valid CEX witness => `outcome: refuted`, never `proved`.
- Non-Lean evidence classes use explicit N/A sentinels — never fake hashes.
- Today eligible for theorem CR: `algebra.ideal_membership_witness`,
  `algebra.rational_equality`, `algebra.linear_algebra` (`proved`),
  `logic.finite_counterexample` (`refuted`),
  `algebra.formal_rational_calculus` (`proved`), and
  `analysis.analytic_calculus` (`proved`). Federated logic stays
  `crEligible=false`.

---

## 9. Exact replay generation / offline lifecycle

### Generator framework (SPEC-03)

Package: [`adapters/common/exact_replay/`](../adapters/common/exact_replay/).

```text
raw candidate
  -> parse_and_validate -> CanonicalCandidate
  -> to_replay_ir -> ReplayIR
  -> render -> GeneratedModule (+ hash)
  -> verify (pinned lake/lean; caller-owned)
  -> bind -> AssuranceEvidence
```

Plugins register per capability (ideal, rational equality, LA, CEX, formal /
analytic calculus). Scripts under `scripts/generate_exact_*_replay_module.py`
are thin entrypoints. Typed IR constructors only — no raw caller Lean fragments.

### Offline release bundle (SPEC-09)

Driver: [`scripts/offline_exact_replay.py`](../scripts/offline_exact_replay.py).

Bundle binds: canonical candidate, CR (when present), replay manifest, generated
source or regeneration inputs, generator/grammar versions, toolchain contract,
dependency lock, artifact hashes, expected declaration identity, execution-policy
id, driver version. No absolute local paths as semantic fields.

Two modes, same logical outcome: **regenerate-and-verify** and
**artifact-replay**. After materialization, network disabled
(`MATHEVIDENCE_OFFLINE=1`). Missing deps => setup/integrity error, not theorem
failure.

---

## 10. Status table (registry-backed)

Authoritative source:
[`registry/maturity-inventory.json`](../registry/maturity-inventory.json).
The table in [`STATUS.md`](STATUS.md) is validated against that inventory
(`python scripts/validate_maturity_inventory.py`). Hand edits must not invent
`cr_eligible=true`.

All six exact-bound owned capabilities are **`cr_eligible=true`** after local
Lean E2E. Federated logic remains false.

| Capability | exactBinding / exact_candidate_binding_exists | offline_replay_exists | cr_eligible |
| --- | --- | --- | --- |
| `algebra.ideal_membership_witness` | **true** | true | **true** |
| `algebra.rational_equality` | **true** | true | **true** |
| `algebra.linear_algebra` | **true** | true | **true** |
| `logic.finite_counterexample` | **true** | true | **true** (`refuted`) |
| `algebra.formal_rational_calculus` | **true** | true | **true** |
| `analysis.analytic_calculus` | **true** | true | **true** |
| `logic.sat_unsat` | false | false | false |
| `logic.pseudo_boolean` | false | false | false |
| `logic.smt` | false | false | false |

Exact binding means a typed generator exists and is registered — **not** that
Lake E2E or CR minting is authorized (except where `cr_eligible` is true).

---

## 11. Known limitations

| Limitation | Status |
| --- | --- |
| Lake / Lean exact-replay CI (SPEC-01) | Local lean.yml targets + exact E2E green for all six owned exact-bound capabilities after olean-path / declaration-identity argv / renderer / Checkers barrel ReplaySound imports. Remote Actions on the pin may still lag until this branch is pushed. |
| `crEligible` | **true** for ideal, rational equality, LA (4 ops), CEX (`refuted`), formal rational calculus (4 ops), analytic calculus (Deriv/DerivWithin/Antideriv/ODE empty-obligation single-IC); federated false |
| Analytic ODE IC constraints | Exact ODE whitelist: empty domain obligations + at most one initial condition; multi-IC / obligation-bearing ODE fail closed |
| Offline exact theorem inspect | Defaults to `theorem_pending`; `MATHEVIDENCE_OFFLINE_LEAN=1` / `require_lean=True` can yield `theorem_proved` after identity inspect — still not a CR mint; online `kernel_replay` is promotion authority |
| Formal vs analytic calculus | Separate IDs; formal is not `HasDerivAt` / analytic ODE |
| Federated SAT / PB / SMT | Metadata only; never CR-eligible in this program |
| Signing / third-party reproduction | Explicitly **deferred**; bundle format must stay usable later without hidden local state |
| Historical `MET` / audit language | Dated records only — not current CR authority |
| Windows Lake link | rsp path required for some exes; degrade honestly |

Authoritative gap list: [`security/KNOWN_TRUST_GAPS.md`](security/KNOWN_TRUST_GAPS.md).

---

## 12. Incident / triage workflow

| Failure class | First investigation |
| --- | --- |
| schema / conformance | candidate/evidence schema and adapter contract |
| Lean build | toolchain, dependency closure, generated module, import/declaration, ExprSerialize |
| exact replay | candidate binding, generator, manifest, verifier identity |
| offline replay | dependency materialization, network assumptions, bundle integrity |
| benchmark | only benchmark logic/data **after** assurance/replay prerequisites are green |
| security | execution bounds, input validation, path/process handling |
| supply chain | locks / vendor hashes / dependency provenance |

Do not close a Lean red with a benchmark green narrative. Do not treat
`assurance_mode_unavailable` as a solver bug.

---

## Capability onboarding checklist

Every new (or newly exact-enabled) capability must execute:

```text
[ ] define capability ID/version and evidence class
[ ] define canonical candidate/evidence schema
[ ] implement adapter
[ ] implement/check evidence checker
[ ] state exact mathematical proposition and semantic domain
[ ] add Lean/reference soundness contract where exact theorem assurance is intended
[ ] add typed exact replay translation/generator
[ ] register verifier/generator/grammar versions
[ ] add exact E2E positive/negative tests
[ ] add candidate mismatch / fixture substitution tests
[ ] add offline replay bundle test
[ ] add bounded-execution/adversarial tests
[ ] update registry (assurancePolicy + maturity-inventory)
[ ] enable CR eligibility only after all applicable gates pass
[ ] update generated/validated docs (STATUS.md table must stay registry-backed)
```

Enablement order: checker, Lean contract, exact binding, exact E2E, offline
replay, tamper, then policy `crEligible` (last). Checker-only PRs must not
claim certification complete.

---

## How not to lie about assurance

| Tempting claim | Honest statement |
| --- | --- |
| Checker passes | Evidence checker accepted; **not** a theorem CR |
| Fixture / OfflineFixtures theorem passes | Protocol self-test; not the submitted candidate proved |
| Numerical / float agreement | Evidence-only; not an exact proof |
| No counterexample found | Search failed; not theorem true / `proved` |
| Benchmark suite green | Task metrics; not assurance / `crEligible` |
| Formal rational calculus works | Formal/algebraic fragment only; not arbitrary analytic calculus |
| Exact generator exists | Binding supported in registry; not CR-eligible until gates pass |
| Offline bundle rebuilds | Regenerability; default `theorem_pending`; opt-in Lean inspect may yield `theorem_proved` but does **not** mint a CR |
| Analytic ODE accepted | Empty-obligation single-IC whitelist only; not existence/uniqueness |

---

## Maintenance rule

Status documentation must be **generated from or validated against** the
capability registry / maturity inventory. Narrative context is fine; independently
asserting `cr_eligible=true` in prose is not. Validators:

- `python scripts/validate_registry.py`
- `python scripts/validate_maturity_inventory.py`

Registry increases of assurance are security-sensitive reviews.

---

## Deferred (out of this program)

Independent third-party reproduction, human governance gates, and final
release-signing / attestation policy remain deferred. Do not document them as
complete. Keep bundle and registry formats free of hidden local-only state so
those workstreams can attach later.
