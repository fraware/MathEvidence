# Standalone specification — trusted path and kernel replay


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Objective

Implement a theorem-producing replay path whose verified status is justified by an actual Lean declaration accepted by the kernel in a recorded environment.

## Required architecture

The repository MUST expose two distinct executables.

### `mathevidence-verify-bundle`

This executable performs operational validation only:

1. Resolve a bundle ID inside a configured store.
2. Parse the canonical manifest.
3. Verify manifest-defined file content digests.
4. Parse and validate the request and certificate schemas.
5. Recompute the request digest.
6. Decode the domain certificate.
7. Execute the Lean checker.
8. Emit a `CheckerEvaluation` record.

Its maximum assurance is `native_checked`. Its positive result status is `checker_accepted`. It MUST NOT emit `claimEstablished`, `soundness_verified`, or `kernel_replay`.

### `mathevidence-kernel-replay`

This executable or generated-module driver performs theorem certification:

1. Resolve the immutable candidate bundle by bundle digest.
2. Parse a `ReplayTarget` identifying the exact original Lean theorem type.
3. Elaborate the theorem type in a pinned Lean environment.
4. Reify the theorem type into the domain IR.
5. Prove that the reified request equals the bundle request.
6. Recompute and compare the request digest.
7. Decode the certificate.
8. Apply the checker soundness theorem.
9. Discharge explicit side conditions using hypotheses already present in the theorem type or return unresolved obligations.
10. Construct a theorem declaration with a stable generated name.
11. Add the declaration to the environment and require kernel acceptance.
12. Query the declaration’s axiom dependencies.
13. Emit an immutable `CertificationRecord`.

A subprocess that merely evaluates `checkBool` does not satisfy this specification.

## Replay target representation

Add `MathEvidence/Core/ReplayTarget.lean` and `schemas/replay-target.schema.json`.

The target MUST contain:

- `schemaVersion`
- `moduleName`
- `declarationName`
- `theoremTypeCanonical`
- `theoremTypeDigest`
- `sourceRevision`
- `sourceFile`
- `sourceSpan`
- `environmentLockDigest`
- `capability`
- `requestDigest`

The canonical theorem type MUST be derived from elaborated Lean syntax after universe metavariables and implicit parameters are resolved. Pretty-printed source text alone is insufficient.

## Theorem type digest

Implement `MathEvidence/Core/TheoremIdentity.lean`.

The digest input MUST include:

- fully elaborated expression serialization;
- universe level parameters;
- local binder types and binder information;
- reducibility-normalized constant names;
- imported environment lock digest.

The first release MAY use a stable Lean-owned structural serializer. It MUST include version metadata and test vectors. A future serializer change requires a theorem-identity schema version increment.

## Rational theorem construction

Refactor rational replay around a theorem:

```lean
theorem replaySound
    (goal : ReifiedGoal)
    (req : Request)
    (cert : Certificate)
    (hGoal : goal.toClaim = req.claim)
    (hReq : req = Request.ofClaim goal.toClaim)
    (hCheck : checkBool req cert = true)
    (hConditions : GoalConditions goal cert.denomFactors) :
    goal.originalProp
```

The proof MUST use:

- the reifier’s semantic correctness theorem;
- `checkBool_sound`;
- a theorem mapping certificate denominator factors to the original local hypotheses;
- no independent `ring` invocation that proves the goal without the checker theorem.

A final `ring` call MAY appear inside a proved normalization lemma used by the checker. It may not serve as an unrelated second proof path after acceptance.

## Generated replay module

Add `scripts/generate_replay_module.py` only as an untrusted code generator. It must generate a Lean module with:

- pinned imports;
- the exact theorem target;
- the decoded request and certificate as data;
- digest equality proofs;
- one theorem whose body applies the domain soundness theorem;
- `#print axioms` or an environment query for the generated declaration.

The generated module MUST be compiled by `lake env lean`. Generation failure, compile failure, theorem mismatch, or unexpected axioms MUST reject certification.

## Certification record

A successful kernel replay MUST emit:

- candidate bundle digest;
- replay target digest;
- theorem declaration name;
- theorem type digest;
- proof declaration digest;
- checker declaration and soundness theorem names;
- request and certificate content digests;
- environment lock digest;
- axiom report digest;
- claim requested and established;
- unresolved obligations;
- assurance mode `kernel_replay`;
- result status `soundness_verified` or the exact supported stronger class.

The record MUST be written outside the candidate bundle.

## Error taxonomy

The kernel replay command MUST use stable error codes:

- `bundle_not_found`
- `manifest_invalid`
- `content_digest_mismatch`
- `request_decode_failed`
- `certificate_decode_failed`
- `request_digest_mismatch`
- `goal_reification_failed`
- `goal_claim_mismatch`
- `checker_rejected`
- `side_condition_unresolved`
- `theorem_elaboration_failed`
- `kernel_rejected`
- `unexpected_axiom`
- `environment_mismatch`
- `resource_limit_exceeded`

Catch-all conversion to `bundle_not_found` is forbidden.

## Tests

### Positive

- Rational equality example produces a declaration with the expected theorem type.
- The declaration’s axiom report contains only explicitly allowed imported axioms.
- Certification succeeds without SymPy, Mathematica, Sage, or Python adapter execution.
- Replaying the same immutable inputs produces byte-identical certification payloads, excluding an optional external signature envelope.

### Negative

- Same certificate with changed theorem target.
- Same request with changed environment lock.
- Certificate content altered after manifest creation.
- Theorem file altered after certification.
- Missing denominator hypothesis.
- Added local hypothesis that changes theorem type.
- Reordered or renamed variables where semantics differ.
- Unsupported theorem syntax.
- Checker accepted custom IR but reifier semantic bridge deliberately corrupted in a test fixture.
- Unexpected axiom injected into generated declaration.

### Cross-language parity

- Lean, Python, and JavaScript must agree on request, bundle, theorem target, and certification-record digests for published vectors.
- Duplicate JSON keys, alternate line endings, Unicode key ordering, and integer edge cases must be covered.

## Acceptance

This work is complete only when:

- `mathevidence-verify-bundle` never emits theorem-level status.
- `mathevidence-kernel-replay` compiles a declaration for the original theorem.
- The receipt identifies true theorem and bundle digests.
- Agent and Studio consume only certification records for Certified status.
- CI runs positive and negative kernel replay cases on every trust-path change.
