# Standalone specification — flagship ideal-membership witness capability


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Strategic purpose

Ideal-membership witness checking should become the first capability that demonstrates the full MathEvidence value proposition. External systems search for multiplier polynomials. Lean checks one compact identity and converts it into an ordinary Mathlib ideal-membership theorem.

The capability should be called `algebra.ideal_membership_witness`. Keep `algebra.groebner_membership` only if the project later checks a Gröbner-basis or reduction certificate with corresponding semantics.

## Mathematical contract

For a commutative ring `R`, finite variable type `σ`, target `f`, generators `g : Fin n → MvPolynomial σ R`, and multiplier witness `q : Fin n → MvPolynomial σ R`, the certificate relation is:

```lean
f = ∑ i, q i * g i
```

The established theorem is:

```lean
f ∈ Ideal.span (Set.range g)
```

The first stable fragment SHOULD use:

- coefficient ring `ℤ` or `ℚ`;
- variable type `Fin m`;
- explicit finite generator vector;
- witness claim only;
- no Gröbner basis, radical membership, ideal equality, minimality, or completeness.

## Typed sparse IR

Replace list-shaped exponent vectors with fixed-arity monomials.

Recommended representation:

```lean
structure Monomial (m : Nat) where
  exponents : Fin m →₀ Nat

structure Term (m : Nat) where
  coeff : Int
  monomial : Monomial m

structure SparsePoly (m : Nat) where
  terms : Array (Term m)
  canonical : CanonicalTerms terms
```

If dependent canonicality is too expensive for executable data, use:

```lean
structure RawSparsePoly (m : Nat) where
  terms : Array (Term m)

def normalize : RawSparsePoly m → SparsePoly m
```

and prove normalization semantics.

Negative exponents and exponent-vector truncation must be impossible by construction. Python and JSON decoders must reject any exponent array whose length differs from `varCount`.

## Interpretation

Add `MathEvidence/IR/Polynomial/Interpret.lean`.

Define:

```lean
def Monomial.toMvMonomial :
    Monomial m → (Fin m →₀ Nat)

def SparsePoly.eval :
    SparsePoly m → MvPolynomial (Fin m) ℤ
```

Prove:

- `eval_zero`
- `eval_one`
- `eval_add`
- `eval_neg`
- `eval_sub`
- `eval_mul`
- `eval_pow`
- `eval_normalize`
- `eval_linearCombination`

The proof may reuse Mathlib finite-support and MvPolynomial lemmas. All computational normalization code must have a semantic preservation theorem.

## Request and certificate

Add Lean structures:

```lean
structure Claim where
  varCount : Nat
  target : SparsePoly varCount
  generators : Array (SparsePoly varCount)
  claimClass : ClaimClass := .witness

structure Request where
  capability : CapabilityRef
  claim : Claim
  resourcePolicy : ResourcePolicy
  requestDigest : RequestDigest

structure Certificate where
  requestDigest : RequestDigest
  multipliers : Array (SparsePoly varCount)
```

The certificate length must equal the generator length.

The request digest must be Lean-derived from the exact canonical wire representation.

## Checker

Define:

```lean
def checkBool (req : Request) (cert : Certificate) : Bool :=
  digestOk req cert &&
  wellFormed req cert &&
  resourceOk req cert &&
  linearCombination req.claim.generators cert.multipliers =
    req.claim.target
```

Prove:

```lean
theorem checkBool_identity
    (h : checkBool req cert = true) :
    req.claim.target.eval =
      ∑ i, (cert.multipliers[i]).eval * (req.claim.generators[i]).eval

theorem checkBool_sound
    (h : checkBool req cert = true) :
    req.claim.target.eval ∈
      Ideal.span (Set.range fun i => (req.claim.generators[i]).eval)
```

This theorem is the authority. The tactic must close the user goal by applying it.

## Reification correctness

Meta reification code must produce a proof object or a reification certificate connecting the original polynomial expression to `SparsePoly.eval`.

For each reified expression `e`, return:

- IR polynomial `p`;
- theorem term `h : p.eval = e`.

The reifier must compose proofs for constants, variables, addition, subtraction, multiplication, powers, and supported casts. Unsupported coefficient rings or variable types must fail.

For an `Ideal.span` goal, return:

- target equality proof;
- each generator equality proof;
- exact finite-set/set-range equivalence proof;
- goal transport theorem.

## Tactic architecture

`mathevidence_ideal` must support:

```text
mathevidence_ideal
mathevidence_ideal (backend := sympy)
mathevidence_ideal (backend := sage)
mathevidence_ideal (backend := mathematica)
mathevidence_ideal replay <bundle-id>
```

Execution:

1. reify goal with proof-producing reifier;
2. build Lean-derived request;
3. query selected backend only in discovery mode;
4. decode certificate;
5. check request digest and certificate;
6. prove `checkBool = true`;
7. apply `checkBool_sound`;
8. transport through reification equalities;
9. close original goal;
10. emit Candidate Bundle and Certification Record.

Internal witness search is retained as a baseline backend named `lean_reference_search`. It must never masquerade as SymPy or Mathematica.

## Backend requirements

### SymPy

- Use exact `QQ` or `ZZ` domains.
- Return rational coefficients when the request ring is `ℚ`.
- Reject domain promotion.
- Validate variable ordering.
- Return detailed failure codes.
- Avoid broad exception-to-None handling.

### Sage

- Use explicit polynomial rings with fixed variable order and base ring.
- Record Sage and Singular versions.
- Return multiplier witnesses only.
- Add live conformance in an environment where Sage is installed.

### Mathematica

- Use fixed `wolframscript` arguments.
- Encode declared variables without raw name interpolation.
- Obtain a representation of ideal-membership coefficients.
- Convert to the restricted IR.
- Record `$Version` and adapter version.
- Retain committed offline fixtures for public replay.

## Benchmark redesign

The benchmark pass condition is:

```text
backend proposes witness
AND Lean decoder accepts
AND Lean checker accepts proposed witness
AND kernel theorem replay closes the original Mathlib goal
```

The committed `expectedMultipliers` are an oracle for benchmark validation only. They cannot substitute for backend output.

Required benchmark sets:

1. `unit` — 20 small deterministic cases.
2. `adversarial` — malformed exponents, variable order, coefficient domain, wrong witness length, overflow/resource cases.
3. `synthetic-held-out` — generator families excluded from adapter development.
4. `library-derived` — at least 20 obligations extracted from Mathlib, CSLib, Physlib, SciLean, or real formalization branches with provenance.
5. `scale` — degree, variable count, generator count, and coefficient-bit-size sweeps.

Required baselines:

- `ring` or native Mathlib proof where applicable;
- Lean reference search;
- SymPy;
- Sage;
- Mathematica.

Metrics:

- proposal success;
- decoder acceptance;
- checker acceptance;
- theorem closure;
- false acceptance;
- median and p95 search time;
- checker time;
- evidence bytes;
- proof compilation time;
- resource-limit outcomes;
- backend disagreement.

A 50-task numeric threshold is insufficient. At least 70% of the release benchmark must be nontrivial and deduplicated by normalized claim shape.

## Capability lifecycle

Registry promotion to `candidate` requires:

- proved checker soundness;
- request/certificate schemas;
- at least two backends;
- corrected benchmark;
- offline replay;
- no placeholders;
- independent domain review.

Promotion to `stable` additionally requires:

- one external Lean project adoption;
- real workflow win;
- protected CI attestation;
- two-area review;
- a versioned release artifact.

## Acceptance

The flagship is complete only when removing the external certificate prevents the supported nontrivial theorem from closing, checker acceptance directly implies the Mathlib goal, and the corrected benchmark measures backend-proposed witnesses.
