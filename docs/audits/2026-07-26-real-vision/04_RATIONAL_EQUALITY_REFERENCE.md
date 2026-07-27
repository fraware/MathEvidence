# Standalone specification — rational equality reference capability


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Role

`algebra.rational_equality` is the protocol-reference capability. It validates request binding, typed semantic translation, explicit side conditions, multi-backend normalization, offline replay, checker soundness, and error reporting. It is not the project’s primary evidence of valuable external search.

Set registry fields:

```json
"role": "protocol_reference",
"externalSearchEssential": false
```

## Required changes

### Remove the zero-digest fallback

Change `Request.ofClaim` to return `Except RequestEncodingError Request`. Prove or test totality for all well-formed `Claim` values. No constructor may fabricate an all-zero digest.

### Enforce resource limits in Lean

Add a checked request policy containing:

- maximum variable count;
- maximum expression nodes;
- maximum exponent;
- maximum integer digits;
- maximum denominator factors;
- maximum normalized term count.

`checkBool` must reject before expensive normalization when limits are exceeded. The policy itself participates in request binding.

### Formalize denominator obligation matching

Structural equality is acceptable for the initial stable fragment only if the request schema states that certificate factors must reproduce original division-denominator subexpressions exactly.

A future factor-equivalence mode requires:

- a separate factor certificate;
- proof that each original denominator is a product of certified factors;
- proof that nonzero factors imply denominator nonzero.

Do not silently mix structural and algebraic coverage.

### Make checker soundness the proof authority

The theorem-producing tactic must:

1. reify the current goal;
2. construct the request;
3. decode the certificate;
4. prove `checkBool req cert = true`;
5. invoke `checkBool_sound`;
6. instantiate the resulting universal proposition at the current variables;
7. prove `conditionsHold` from local hypotheses;
8. transport the IR equality to the original Lean equality using the reifier semantic theorem.

The tactic may use automation to prove side conditions. It must fail with an explicit list of unresolved conditions.

### Generic bundle lookup

Replace the `BundleId` enumeration as the primary mechanism. Support:

- content-addressed bundle ID;
- request-digest index lookup;
- explicit backend preference;
- deterministic selection policy;
- exact capability/version filtering.

Keep named fixture IDs only in tests.

### Status report

A successful tactic report must include:

- original theorem type digest;
- request digest;
- candidate bundle digest;
- certification record digest;
- backend provenance;
- claim requested and established;
- exact side conditions used;
- checker and soundness theorem names;
- assurance mode;
- axiom report summary.

### Conformance

Maintain SymPy and Mathematica shared-checker coverage. Add cases for:

- repeated denominators;
- scalar rational denominators;
- nested division;
- variable permutation;
- non-ASCII variable rejection;
- maximum-size boundary;
- exponent boundary;
- known assumptions that cover only part of the required set;
- certificate with an extra irrelevant factor;
- algebraically equivalent but structurally different factor;
- positive-characteristic scope rejection if the capability remains over `ℚ`.

## Acceptance

Rational equality is complete when both the tactic and kernel replay construct the original theorem through the checker soundness theorem, every resource bound is enforced in Lean, and external-backend absence does not affect replay.
