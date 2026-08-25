# Reproducibility protocol

This document defines how to reproduce an experimental MathEvidence release
without confusing repository reproducibility, evidence replay, and theorem
certification.

## 1. Identify the exact revision

Record the release tag and resolved Git commit before running anything. A release
artifact must be traceable to one immutable commit. `scripts/generate_release_provenance.py`
records the commit/tree and hashes the assurance-relevant repository surface.

Do not reproduce from an unspecified moving branch and call the result release
reproduction.

## 2. Materialize pinned dependencies

Use the committed `lean-toolchain`, `lake-manifest.json`, `uv.lock`, and project
metadata. Dependency installation may require network access during initial
materialization. After materialization, offline-replay claims apply only to the
scope explicitly described in the maturity inventory.

Typical setup:

```text
bash scripts/ci/install-elan-pinned.sh
uv sync --frozen --extra dev --extra sympy
```

## 3. Validate the trust surface

Before evaluating benchmark or theorem claims, validate schemas, capability
registries, maturity policy, import boundaries, and proof-audit constraints:

```text
python scripts/validate_schemas.py
python scripts/validate_registry.py
python scripts/validate_maturity_inventory.py
python scripts/check_import_boundaries.py
python scripts/audit_sorry_axioms.py
```

A validation failure is a setup/integrity failure, not a mathematical rejection.

## 4. Build the pinned Lean trust path

Build the verification executables and audit drivers with the pinned toolchain:

```text
lake build \
  mathevidence-verify-bundle \
  mathevidence-kernel-replay \
  mathevidence-declaration-identity \
  mathevidence-import-graph \
  mathevidence-axiom-report
```

Then run the environment-level import/axiom audits used by CI.

## 5. Reproduce candidate-specific exact assurance

For theorem-level Certification Record eligibility, structural source generation
is insufficient. The release gate must generate the exact candidate-specific Lean
module through the production exact-replay plugin and successfully elaborate it
with the pinned Lean environment:

```text
python scripts/ci/run_cr_exact_lean_e2e.py
```

The script derives the CR-eligible capability set from
`registry/maturity-inventory.json`. For operation-discriminated capabilities it
also requires coverage of the complete production exact-operation/whitelist set.
Adding a promoted exact form without an E2E case therefore fails release CI.

## 6. Reproduce offline bundle integrity separately

Offline bundle replay checks canonical inputs, generated source, manifests,
artifacts, toolchain contracts, and tamper resistance without relying on a live
CAS backend:

```text
MATHEVIDENCE_OFFLINE=1 python -m pytest tests/forensic/test_offline_exact_replay.py -q
```

`offline_bundle_replay_exists` does not imply
`offline_kernel_replay_exists`. A result such as `theorem_pending` is not a
kernel theorem proof and must not be relabeled.

## 7. Reproduce benchmarks without assurance escalation

Run the benchmark workflows/commands only as empirical task-performance evidence.
Benchmark pass/fail never changes Certification Record eligibility and cannot
replace exact candidate replay.

The ideal-membership suite is a frozen conformance/regression corpus. Its results
must not be generalized into a claim that arbitrary external solver output is
sound.

## 8. Generate and inspect release provenance

Generate the release manifest:

```text
python scripts/generate_release_provenance.py dist/provenance
```

Verify that the manifest records the exact Git revision, Lean toolchain, Lake
package pins, and hashes of the assurance-relevant registry/schema/workflow/lock
and evidence surfaces. Compare artifact digests before relying on copied release
files.

## 9. Interpret outcomes correctly

Use these categories consistently:

- **proved** — the declared exact proposition for the submitted candidate passed the trusted theorem path;
- **refuted** — a certified counterexample establishes falsity of the scoped claim;
- **evidence-only / checker accepted** — useful evidence without theorem-level promotion;
- **tamper/setup/integrity error** — replay environment or artifact integrity failed;
- **unavailable** — the requested assurance mode is not supported and no stronger label may be retained.

A compiler/dependency/setup failure is not a theorem rejection. Absence of a
counterexample is not a proof. Numerical agreement is not exact proof.

## 10. Release acceptance

An experimental release should be created only from a frozen commit after its
required CI matrix is green. Stable capability promotion is governed separately
and requires the additional human/external artifacts documented in the stable
promotion checklist; experimental release readiness does not satisfy those gates.
