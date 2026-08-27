# Changelog

All notable changes to the MathEvidence experimental 0.x line are documented here.
The project remains experimental: this file does not promote any capability to
`stable` and does not supersede `registry/maturity-inventory.json`.

## [Unreleased]

### Assurance and exact replay

- Rebased theorem-level Certification Record eligibility on exact submitted-candidate binding.
- Added registry-driven exact replay policy with fail-closed unsupported modes and no exact-to-fixture fallback.
- Added deterministic typed exact-replay generators for the currently CR-eligible owned capabilities.
- Added candidate-specific Lean E2E execution as a release gate and coupled its coverage to the maturity inventory and production operation whitelists.
- Preserved explicit result polarity: finite counterexamples certify `refuted`, not `proved`.
- Separated deterministic offline bundle replay from offline kernel theorem replay in maturity reporting.
- Strengthened Certification Record binding to candidate, request, generated source, generator/grammar, verifier identity, toolchain/dependency contracts, and replay provenance.

### Trust and security

- Kept adapters, generators, model outputs, and submitted evidence outside the trusted theorem boundary.
- Hardened generated replay around typed IR, bounded execution, argv-only process spawning, output/time limits, path controls, and tamper tests.
- Preserved sorry/axiom/import/declaration-identity audits and prevented fixture substitution from serving as Certification Record authority.
- Kept benchmark outcomes independent from theorem-level assurance eligibility.

### Reproducibility and release engineering

- Added machine-readable maturity inventory validation and status-document drift checks.
- Strengthened release provenance to bind the exact repository revision, toolchain/dependency pins, registry/schema trust surface, and release evidence.
- Added release-oriented citation and reproducibility documentation.
- Removed temporary audit scratch material from the release tree.

### Scope

The experimental exact-certification surface is intentionally narrow. Consult
`docs/STATUS.md` and `docs/security/KNOWN_TRUST_GAPS.md` for the proposition
established by each capability and for unsupported claims. Human stable-promotion,
external reproduction, independent semantic review, production signing/PKI, and
other governance gates remain separate unless a later release records completed
artifacts for them.
