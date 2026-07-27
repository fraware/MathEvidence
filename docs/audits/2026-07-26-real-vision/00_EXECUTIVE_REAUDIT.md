# Executive re-audit


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Bottom line

MathEvidence now has a coherent experimental architecture and several useful restricted demonstrations. The repository contains real Lean definitions, executable checkers, Meta reifiers, backend adapters, a content-aware bundle format, an Agent API, Studio status rules, adversarial tests, a sizeable generated Foundry corpus, and a new ideal-membership vertical. The engineering effort since the previous audit is substantial.

The repository still falls short of its own North Star at the exact point where evidence must become an ordinary Lean theorem. The current implementation often uses a checker as a gate, then proves the user goal through an independent tactic such as `ring` or `native_decide`. The standalone replay executable performs content checks and evaluates `checkBool`, then emits `soundness_verified` without constructing a theorem term or importing a checker soundness theorem. This distinction is foundational. A Boolean executed by a Lean binary is not automatically a kernel-checked proof of the original proposition.

## What materially improved

### Request binding

`MathEvidence/Core/Digest/Types.lean` introduces nominal digest types. `MathEvidence/Checkers/RationalEquality/Wire.lean` derives the request digest from a Lean-owned wire representation. `MathEvidence/Tactic/Discovery.lean` now rejects an adapter certificate whose digest differs from `Request.ofClaim c`. This repairs the earlier live-discovery digest substitution defect.

### Theorem-goal matching in the tactic

`MathEvidence/Tactic/Replay.lean` reifies the current rational equality goal, compares it with the bundle claim, checks the certificate, and refuses mismatched goals. `MathEvidence/Tactic/Mathevidence.lean` no longer closes `True` as a stand-in for theorem replay.

### Public path safety

`agent/api/bundle_store.py` rejects absolute paths, traversal, backslashes, and unregistered bundle identifiers. Public Agent operations use opaque bundle IDs.

### Honest public documentation

`README.md`, `docs/STATUS.md`, `docs/security/KNOWN_TRUST_GAPS.md`, `GOVERNANCE.md`, and `.github/CODEOWNERS` consistently identify the project as experimental, acknowledge single-owner incubation, and block stable promotion.

### Cross-domain demonstrations

Restricted Meta reifiers and tactics now exist for rational expressions, concrete matrices, finite predicates, and polynomial ideal-membership goals. The repository also separates `algebra.formal_rational_calculus` from `analysis.analytic_calculus`.

## Critical findings

### P0-A — Standalone replay does not produce a theorem

`MathEvidence/Exe/Replay.lean` verifies files, decodes rational requests and certificates, recomputes a request digest, and evaluates `checkBool`. It does not import `RationalEquality.Soundness`, construct a proof of `Claim.proposition`, elaborate the original theorem source, or ask the kernel to accept a new declaration. It nevertheless emits `kernel_replay` and `soundness_verified`.

Required decision:

- Rename the current executable to a bundle verifier and report `native_checked` or `checker_accepted`.
- Build a separate kernel replay executable or generated-module workflow that elaborates an exact theorem and applies a soundness theorem.
- Prevent Agent and Studio from treating the current executable as theorem authority.

### P0-B — Receipt digests are not truthful

`MathEvidence/Tactic/Replay.lean` sets `bundleDigest` and `theoremDigest` to the request digest. `MathEvidence/Exe/Replay.lean` sets `theoremDigest` to the request digest and computes `bundleDigest` from the manifest file alone. These fields do not identify the theorem or complete bundle.

Required decision:

- Make each digest derive from the bytes or canonical semantic object named by its type.
- Remove every fallback that substitutes one digest class for another.
- Reject receipts whose theorem, bundle, certificate, axiom, or environment digests cannot be independently recomputed.

### P0-C — Bundles contain deliberate theorem and axiom placeholders

`adapters/common/bundle.py` writes a default theorem declaring `True` and a default axiom report with `pending_compiled_audit`. Existing example and conformance bundles contain those files.

Required decision:

- Candidate bundles must omit theorem and axiom roles.
- Certified records must contain a real theorem declaration and compiled axiom report.
- The migration must reclassify every existing v0.2 bundle according to the evidence it actually contains.

### P0-D — Content-addressed storage is keyed by request digest

`BundleStore.commit_content_addressed` derives the storage identifier from `requestDigest`. Two independent certificates for the same request collide, and the existing directory wins without byte equality verification.

Required decision:

- Define a canonical bundle digest.
- Key storage by that digest.
- Detect and hard-fail same-ID/different-bytes collisions.
- Preserve request digest as an index, allowing one request to map to multiple bundles.

### P0-E — Ideal membership lacks a formal semantics bridge

The flagship checker proves equality inside a custom sparse polynomial implementation. The tactic then reconstructs Lean polynomial syntax and separately invokes `ring`. No theorem connects checker acceptance to the Mathlib ideal-membership goal.

Required decision:

- Formalize interpretation of the sparse IR into `MvPolynomial` or `Polynomial`.
- Prove normalization, addition, multiplication, and linear-combination soundness.
- Prove checker acceptance implies Mathlib ideal membership.
- Close the goal by applying that theorem, with no independent `ring` proof serving as the actual authority.

### P0-F — The ideal-membership benchmark does not score backend output

`scripts/run_ideal_membership_benchmark.py` validates the committed `expectedMultipliers` for ordinary pass tasks. It records whether the proposed witness was accepted but does not use that value to determine task success.

Required decision:

- Pass a task only when the backend-proposed multipliers pass the Lean-owned checker and theorem bridge.
- Separate oracle validation from backend evaluation.
- Add realistic held-out tasks and native baselines.

### P0-G — CI is unverified and incomplete

The large closure PR had multiple failed workflows. Later direct commits repaired some migration defects, but the audited head has no attested combined status in the available GitHub status record. Current `just check` also omits the ideal-membership benchmark and the actual replay executable. CI uses regex source scans in place of environment-level audits.

Required decision:

- Establish required checks on protected `main`.
- Run the complete gate on the exact merge commit.
- Include executable replay, ideal membership, forensic tests, compiled import audit, and compiled axiom reporting.
- Commit and enforce the dependency lock.

## High-priority findings

### P1-A — Rational equality remains a protocol reference

Lean recomputes the rational identity internally, and the tactic can close the goal with `field_simp` and `ring`. External computation is useful for testing the protocol but is not essential to solve the supported problem.

Action:

- Retain rational equality as the reference capability.
- Stop using it as evidence that external search unlocks new formal mathematics.
- Use it to validate transport, request binding, failure semantics, side-condition reporting, and replay.

### P1-B — Linear algebra and finite counterexample tactics use parallel proof paths

Both tactics check a custom certificate and then close the original goal through `native_decide` or an explicit proof. The final theorem does not follow through an applied checker-soundness theorem connected to the reified goal.

Action:

- Add reification/interpretation theorems or proof-producing reflection.
- Apply checker soundness to construct the original proposition.
- Retain witness-only scope.

### P1-C — Analytic calculus is scaffolding

`MathEvidence/Checkers/AnalyticCalculus/Basic.lean` contains useful Mathlib derivative examples. Its certificate checker compares syntax and includes an ODE certificate with caller-supplied Booleans. `check_implies_hasDerivTarget` proves only a marker Boolean.

Action:

- Replace the current certificate with a derivative derivation tree.
- Prove by induction that a valid derivation establishes `HasDerivAt` or `HasDerivWithinAt`.
- Encode domain obligations and initial conditions as propositions, not trusted Booleans.

### P1-D — Agent product states remain stronger than their evidence

Hypothesis synthesis calls a Python mirror result `proved`. Conjecture orchestration marks a statement `falsified` from a Python mirror and permits an arbitrary theorem reference to mark `formally_proved`. Trace-to-Plan can accept structurally plausible receipts.

Action:

- Introduce distinct preview states.
- Require a verified certification record for proof-bearing states.
- Remove all transitions driven solely by strings or mirror Booleans.

## Program posture

The project should continue as an experimental research platform. The next phase should concentrate on one complete flagship theorem path, immutable certification artifacts, and reproducible CI. Feature expansion should pause until those foundations close.

The decisive flagship is ideal-membership witness checking because external search can discover a compact witness that Lean checks cheaply. Rational equality should remain the protocol conformance vertical. Analytic calculus should remain experimental until its semantic checker is proved.
