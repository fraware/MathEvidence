# MathEvidence current-main re-audit and real-vision closure package


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Purpose

This package replaces the earlier closure plan with a current-main assessment. The repository changed materially after the earlier audit. Several original P0 defects were repaired, including typed digest wrappers, Lean-side request digest recomputation, theorem-goal matching in the rational replay tactic, bundle path jailing in the public Agent API, registry-driven backend routing, and explicit separation between formal rational calculus and analytic calculus.

The current system is a credible experimental research platform. It is not ready for stable promotion because theorem-level assurance is still overstated in several paths. The central closure objective is to make the following statement literally true for every verified result:

> A concrete original Lean proposition was elaborated, the exact external request was derived from that proposition, the evidence was bound to that request and immutable bundle bytes, a proved checker-soundness theorem was applied to the accepted evidence, the resulting theorem term was accepted by the Lean kernel in a declared environment, and the receipt cryptographically identifies every artifact in that chain.

## Reading order

1. `00_EXECUTIVE_REAUDIT.md`
2. `01_SYSTEM_MAP_WORKING_VS_NOT.md`
3. `02_TRUST_PATH_AND_KERNEL_REPLAY.md`
4. `03_BUNDLE_RECEIPT_AND_CONTENT_STORE.md`
5. `05_IDEAL_MEMBERSHIP_FLAGSHIP.md`
6. `14_ISSUE_BACKLOG_AND_PR_SEQUENCE.md`
7. `15_ACCEPTANCE_MATRIX.md`

The domain and product specifications may then be assigned independently.

## Non-negotiable program decisions

- Stable promotion remains frozen.
- `mathevidence-replay` may not emit `kernel_replay` or `soundness_verified` until it constructs and kernel-checks a theorem for the original elaborated proposition.
- Evidence Bundle v0.2 placeholder theorem and axiom-report roles must be removed from all release-grade bundles.
- The content store must be keyed by a bundle content digest, never by request digest.
- Ideal membership becomes the flagship external-search capability only after a proved sparse-IR-to-Mathlib semantics bridge exists.
- Python checker mirrors may report `mirror_accepted` or `checkable`; they may not report `proved`, `certified`, `falsified`, or `soundness_verified`.
- Every verified Agent or Studio status must derive from a fully verified certification record, not a structurally plausible receipt.
- No capability may be called stable until technical, governance, adoption, and independent-review gates are all complete.

## Files

- `00_EXECUTIVE_REAUDIT.md` — decisive assessment and severity-ranked findings.
- `01_SYSTEM_MAP_WORKING_VS_NOT.md` — component-by-component evaluation.
- `02_TRUST_PATH_AND_KERNEL_REPLAY.md` — theorem-producing replay architecture.
- `03_BUNDLE_RECEIPT_AND_CONTENT_STORE.md` — immutable bundle and certification-record redesign.
- `04_RATIONAL_EQUALITY_REFERENCE.md` — corrected role and proof path.
- `05_IDEAL_MEMBERSHIP_FLAGSHIP.md` — flagship capability specification.
- `06_LINEAR_ALGEBRA_AND_COUNTEREXAMPLE.md` — proof-producing domain closure.
- `07_ANALYTIC_CALCULUS.md` — real Mathlib analytic checker.
- `08_AGENT_API_AND_STUDIO.md` — status, storage, and public-surface hardening.
- `09_HYPOTHESIS_CONJECTURE_TRACE_TO_PLAN.md` — product epistemology corrections.
- `10_FOUNDRY_BENCHMARKS_AND_FEDERATION.md` — data quality and live interoperability.
- `11_SECURITY_CI_RELEASE_TOOLCHAIN.md` — reproducible and attested engineering gate.
- `12_REGISTRY_GOVERNANCE_ADOPTION.md` — machine-enforced lifecycle and human gates.
- `13_FILE_BY_FILE_CHANGE_PLAN.md` — exact repository paths and required changes.
- `14_ISSUE_BACKLOG_AND_PR_SEQUENCE.md` — standalone issues and dependency order.
- `15_ACCEPTANCE_MATRIX.md` — final program exit criteria.
