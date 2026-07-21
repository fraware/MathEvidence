# Evidence Bundle v0.2 migration notes

**Status:** engineering default writers emit v0.2; dual-read of v0.1 remains.  
**Authority:** closure spec 03; gap ledger T5.  
**Updated:** 2026-07-21 (committed Evidence Bundle trees migrated; case-only / federation / foundry excluded).

## Layout

New bundles written by `adapters/common/bundle.py` use canonical `.cjson` bytes
(profile `mathevidence-jcs-0.2`, no pretty whitespace) for theorem-binding roles:

```text
bundle/
  request.cjson
  candidate.cjson
  certificate.cjson
  manifest.cjson
  checker-receipt.cjson   # optional until Lean replay emits it
  theorem.lean
  axiom-report.cjson
  README.md               # optional human rendering
```

Human-readable pretty `.json` copies MAY exist beside these roles; they MUST NOT
be treated as theorem-binding inputs when `.cjson` is present.

## Manifest honesty

- `bundleVersion` is `0.2.0` for new writes (`0.1.0` accepted on read).
- Manifest `resultStatus` MUST NOT be a verified status unless a
  `checker-receipt.cjson` (or legacy `.json`) is present with
  `claimEstablished`.
- `write_bundle` coerces verified statuses down to `computed` when no receipt is
  supplied.
- `scripts/migrate_bundles_v02.py` preserves on-disk `theorem.lean`,
  `axiom-report`, and `checker-receipt`, and promotes manifest
  `resultStatus` when a Lean receipt already establishes a claim.

## Reading old bundles

`verify_bundle_offline`, `mathevidence-replay`, and Agent open/replay resolve
roles with dual path preference:

1. `<role>.cjson`
2. `<role>.json`

## Migrated vs remaining

**Migrated to v0.2** (34 full Evidence Bundle trees via
`scripts/migrate_bundles_v02.py`):

- `evidence/examples/rational_equality_*` (basic + mathematica offline)
- `evidence/examples/linear_algebra_inverse_2x2`
- `evidence/examples/finite_counterexample_nat_eq0`
- `evidence/examples/calculus_*` (5 trees)
- `evidence/examples/ideal_membership_*_offline_*` (4 trees)
- `evidence/conformance/rfc0001/{valid_identity,redundant_condition,variable_permutation,large_coeffs,false_identity,hash_mismatch,missing_condition}/bundle`
- `evidence/conformance/linear_algebra/* /bundle` (6 trees; hash_mismatch adversarial skip-verify)
- `evidence/conformance/finite_counterexample/* /bundle` (4 trees; hash_mismatch adversarial skip-verify)
- `evidence/conformance/symbolic_calculus/* /bundle` (4 trees)

**Not Evidence Bundle trees (intentionally not migrated):**

- `evidence/conformance/**/case.json` + sibling `request.json` case metadata
  (rfc0001 / peer harness inputs — not full request/certificate/manifest bundles)
- `evidence/federation/examples/*.json` and `evidence/federation/agreements/*`
  (federation emit/agreement fixtures, not theorem-binding bundles)
- `evidence/store/sha256/**` content-addressed store objects
- Foundry / conjecture episode corpora (out of scope for theorem-binding v0.2 cut)

**Remaining v0.1 full bundles under `evidence/`:** none.

## Agent / Lean

- `mathevidence-replay` prefers `.cjson`, accepts `.json`, and on rational
  equality success writes `checker-receipt.cjson` (canonical) with
  `claimEstablished` only after digest + `checkBool` + goal match.
- Python packaging remains preview/`tested` when the Lean exe is missing.
- `scripts/generate_lean_offline_fixtures.py` dual-reads `.cjson` / `.json`.

## Checklist for regenerating a fixture tree

1. Re-run the adapter / evidence generator so `write_bundle` emits v0.2,
   or run `python scripts/migrate_bundles_v02.py` for listed trees.
2. Confirm `manifest.cjson` file digests match on-disk `.cjson` / `theorem.lean`.
3. Run `mathevidence-replay --bundle <path>` and confirm receipt emission for
   rational reference cases; re-run migrate if a receipt appears so the
   manifest lists it and may honestly advertise verified status.
4. Update OfflineFixtures / conformance digests only via the documented
   generators — never hand-edit digests.
