# File-by-file change plan


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Core

### `MathEvidence/Core/Digest/Types.lean`

- Make constructors private or expose validated smart constructors only.
- Add theorem or invariant for each digest wire shape.
- Remove direct cross-class construction in downstream code.
- Add parsing tests for uppercase hex, short digests, invalid prefix, and non-hex.

### `MathEvidence/Core/Receipt.lean`

- Replace structural validation with schema-coherent validation.
- Add certificate content, replay target, environment lock, proof declaration, and axiom report digests.
- Enforce claim/result/assurance compatibility.
- Remove any use of request digest as theorem or bundle digest.

### `MathEvidence/Core/Bundle.lean`

- Introduce Candidate Bundle and Certification Record metadata.
- Add role enum and role uniqueness.
- Add bundle digest computation.
- Enforce strict listed-file closure.

### New files

- `MathEvidence/Core/ReplayTarget.lean`
- `MathEvidence/Core/TheoremIdentity.lean`
- `MathEvidence/Core/CertificationRecord.lean`
- `MathEvidence/Core/EnvironmentLock.lean`

## Rational equality

### `MathEvidence/Checkers/RationalEquality/Wire.lean`

- Return `Except` from request construction.
- Remove zero-digest fallback.
- Add complete canonicalization test vectors.

### `MathEvidence/Checkers/RationalEquality/Check.lean`

- Enforce Lean-side resource policy.
- Return structured rejection codes.
- Add explicit structural-factor contract.

### `MathEvidence/Tactic/Replay.lean`

- Apply checker soundness theorem and reifier bridge.
- Remove fake receipt digest assignments.
- Emit a real certification request to the kernel replay subsystem.

### `MathEvidence/Tactic/Discovery.lean`

- Use generic bundle storage/index.
- Keep request digest comparison.
- Separate discovery from theorem certification.

### `MathEvidence/Exe/Replay.lean`

- Rename current behavior to verifier.
- Remove theorem-level status.
- Implement separate kernel replay.
- Stop mutating candidate bundles.
- Improve error taxonomy.

## Bundles and Agent

### `adapters/common/bundle.py`

- Remove default theorem and axiom placeholders.
- Implement v0.3 Candidate Bundle writer.
- Implement strict verification.
- Stop producing dual `.json`/`.cjson` in new artifacts.

### `agent/api/bundle_store.py`

- Key by bundle digest.
- Add request-to-many-bundles index.
- Add collision byte comparison.
- Use atomic commit.

### `agent/api/receipt.py`

- Verify complete Certification Record.
- Require theorem/axiom/environment binding.
- Remove certificate-only verified gate.

### `agent/api/service.py`

- Split compute, verify, kernel replay, and certification open.
- Return IDs only.
- Derive routing from registry.
- Stop treating current replay executable as theorem authority.

### `adapters/common/replay.py`

- Invoke bundle verifier and kernel replay separately.
- Default theorem target cannot be request JSON.
- Never infer Lean authority from executable identity alone.

### `studio/epistemic_contract.py`

- Replace structural receipt Certified gate with verified Certification Record gate.
- Keep structural checks diagnostic-only.

## Ideal membership

### `MathEvidence/IR/Polynomial/Syntax.lean`

- Replace unchecked exponent lists with fixed-arity monomials.
- Add canonical sparse polynomial structure.

### New files

- `MathEvidence/IR/Polynomial/Interpret.lean`
- `MathEvidence/IR/Polynomial/Normalize.lean`
- `MathEvidence/IR/Polynomial/Soundness.lean`
- `MathEvidence/Checkers/IdealMembership/Spec.lean`
- `MathEvidence/Checkers/IdealMembership/Certificate.lean`
- `MathEvidence/Checkers/IdealMembership/Soundness.lean`
- `MathEvidence/Checkers/IdealMembership/Wire.lean`

### `MathEvidence/Checkers/IdealMembership/Check.lean`

- Refactor into checker over typed request/certificate.
- Add resource and well-formedness checks.
- Prove soundness to Mathlib ideal membership.
- Retain search algorithms outside the trusted checker package.

### `MathEvidence/Tactic/ReifyPolynomial.lean`

- Return interpretation equality proof for every expression.
- Reject unsupported rings and variable types.

### `MathEvidence/Tactic/IdealMembership.lean`

- Invoke selected backend in discovery mode.
- Check returned certificate.
- Close by checker soundness theorem.
- Keep internal search as explicit baseline backend.

### `adapters/common/ideal_membership.py`

- Validate arity everywhere.
- Remove exponent `zip` truncation.
- Support exact coefficient domain.
- Preserve structured errors.
- Separate backend proposal from expected witness oracle.

### `scripts/run_ideal_membership_benchmark.py`

- Score proposed multipliers.
- Invoke Lean checker and theorem replay.
- Add baseline and stratified metrics.

### Registry and RFC

- Rename capability unless Gröbner semantics are implemented.
- Update RFC, schemas, support matrix, adapters, and examples atomically.

## Linear algebra and counterexamples

### `MathEvidence/Tactic/ReifyMatrix.lean`
### `MathEvidence/Tactic/ReifyFinitePredicate.lean`

- Return semantic proof objects.

### `MathEvidence/Tactic/LinearAlgebra.lean`
### `MathEvidence/Tactic/Counterexample.lean`

- Apply soundness theorem to original goal.
- Remove independent closing path as authority.
- Emit certification artifacts.

## Analytic calculus

### `MathEvidence/IR/AnalyticExpr/Interpret.lean`

- Complete interpretation and domain semantics.

### `MathEvidence/Checkers/AnalyticCalculus/Basic.lean`

- Split into Spec, Certificate, Check, Soundness, Tests.
- Replace Boolean ODE fields.
- Add derivation-tree soundness.

### New tactic and adapter files

- Add proof-producing reifier.
- Add derivative candidate adapters.
- Add offline replay fixtures only after soundness exists.

## Products

### `agent/hypothesis/__init__.py`

- Rename mirror result states.
- Require certification for proof-bearing lattice entries.

### `agent/conjecture/__init__.py`

- Require certification for falsified/formally proved.
- Rename precision metric.

### `agent/trace_to_plan/__init__.py`

- Use authoritative record verifier.
- Require proof evidence for direct steps.

## CI and governance

### `justfile`

Add:

- executable builds;
- executable positive/negative runs;
- ideal-membership smoke;
- environment import audit;
- environment axiom audit;
- v0.3 migration check.

### `.github/workflows/*.yml`

- Use frozen dependencies.
- Pin all setup actions/installers.
- Run forensic and flagship checks.
- Upload attestation artifacts.
- Require exact-main run.

### `scripts/audit_sorry_axioms.py`

- Expand temporary coverage immediately.
- Deprecate after environment audit lands.

### `scripts/check_import_boundaries.py`

- Add Encoding immediately.
- Deprecate after environment graph audit lands.

### `scripts/validate_registry.py`

- Enforce promotion record and lifecycle coherence.

### `registry/*`, `docs/STATUS.md`, `docs/security/KNOWN_TRUST_GAPS.md`

- Update only after implementation changes land.
- Do not mark gaps closed from file existence alone.
