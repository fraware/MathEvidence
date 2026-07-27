# Standalone specification — exact linear algebra and finite counterexamples


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Shared objective

Convert the existing restricted tactics from “checker gate plus independent proof” into proof-producing evidence workflows.

## Exact linear algebra

### Scope

Retain exact witness claims:

- inverse witness;
- one linear-system solution;
- one nonzero kernel vector;
- determinant identity.

Do not claim rank, kernel-basis completeness, full solution family, uniqueness, or canonical decomposition.

### Reification theorem

For each supported concrete matrix expression, the reifier must return IR data and a theorem equating IR interpretation with the original Mathlib matrix.

Recommended output:

```lean
structure ReifiedMatrixGoal where
  claim : LinearAlgebra.Claim
  originalProp : Prop
  interpretationProof :
    LinearAlgebra.Claim.proposition claim certificatePayload ↔ originalProp
```

A generated proof term is acceptable. A descriptive string is insufficient.

### Checker-to-goal proof

Refactor the tactic:

1. reify goal;
2. build request;
3. decode or construct witness certificate;
4. obtain `checkBool = true`;
5. apply `checkBool_sound`;
6. transport to original goal using the reification theorem.

Remove the final independent `native_decide` as the theorem authority. It may remain in test or normalization lemmas.

### Bundle replay

Add complete request/certificate codecs to the common kernel replay path. Every linear-algebra example must produce a true Certification Record.

### Tests

- dimension mismatch;
- transposed witness;
- left-only inverse;
- right-only inverse;
- zero kernel vector;
- solution with wrong RHS;
- determinant sign error;
- denominator zero;
- resource-limit boundary;
- goal/request mismatch;
- theorem-type digest mismatch.

## Finite counterexamples

### Scope

Retain explicit refutation witnesses. “No witness under a bound” remains `bounded_checked` or `unknown`.

### Semantic bridge

The reifier must return:

- domain interpretation;
- predicate interpretation;
- witness interpretation;
- theorem that `isCounterexample = true` implies the original negated universal or existential-refutation proposition.

For bounded `Int`, the theorem must explicitly carry lower and upper bounds.

### Tactic

The tactic must apply `Counterexample.checkBool_sound` and the reifier bridge. Remove an independent `native_decide` close as the final authority. Direct witness construction is acceptable when it is the formal bridge generated from checker acceptance.

### Agent state

A Python mirror witness may be called:

- `candidate_witness`;
- `mirror_accepted`.

The conjecture becomes `falsified` only after a verified Certification Record for the refutation theorem.

### Tests

- witness type mismatch;
- witness outside domain;
- predicate variable index out of range;
- bound omitted;
- wrong finite cardinality;
- false witness;
- request mismatch;
- budget exhaustion;
- duplicate variable declarations;
- nested quantifier order mismatch.

## Acceptance

Each tactic must produce the original theorem by applying its checker soundness theorem. Every replayable example must have a real theorem identity and axiom report.
