# Standalone specification — analytic calculus vertical


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Objective

Implement a restricted analytic certificate checker whose acceptance proves ordinary Mathlib derivative or ODE propositions.

## Expression semantics

Complete `MathEvidence/IR/AnalyticExpr/Interpret.lean`.

Define interpretation into functions `ℝ → ℝ` for a one-variable initial fragment:

```lean
def Expr.interpret : Expr → ℝ → ℝ
```

For multiple variables, introduce an explicit environment type and delay public support until semantics and reification are proved.

## Domain obligations

Define an inductive obligation type:

```lean
inductive DomainObligation
  | nonzero (expr : Expr)
  | positive (expr : Expr)
  | member (domain : Domain) (expr : Expr)
```

A certificate may produce obligations. The checker does not accept caller-supplied truth Booleans.

## Derivative derivation certificate

Define an inductive tree whose constructors mirror admissible derivative rules:

```lean
inductive DerivProof
  | variable
  | const
  | neg (p : DerivProof)
  | add (p q : DerivProof)
  | sub (p q : DerivProof)
  | mul (p q : DerivProof)
  | inv (p : DerivProof) (obligationId : Nat)
  | div (p q : DerivProof) (obligationId : Nat)
  | pow (k : Nat) (p : DerivProof)
  | sin (p : DerivProof)
  | exp (p : DerivProof)
  | log (p : DerivProof) (obligationId : Nat)
```

The certificate contains source, derivative, proof tree, and obligations.

## Checker and theorem

The checker validates tree shape and reconstructed derivative syntax.

Prove by induction:

```lean
theorem checkDeriv_sound
    (hcheck : checkDeriv cert = true)
    (hdom : SatisfiesObligations cert.obligations x) :
    HasDerivAt cert.source.interpret
      (cert.derivative.interpret x) x
```

For within-domain claims, prove `HasDerivWithinAt`.

The proof must use Mathlib derivative lemmas for every constructor. The current marker theorem must be removed or retained only as a trivial implementation note.

## Antiderivative

An antiderivative certificate is a derivative certificate for the proposed antiderivative. Acceptance establishes `HasDerivAt F f(x) x` under obligations. It does not establish completeness or uniqueness.

## ODE candidate

Replace `residualOk : Bool` and `initialConditionOk : Bool` with:

- interpreted candidate solution;
- RHS expression;
- derivative derivation certificate;
- residual equality certificate;
- initial-condition equality certificate;
- explicit domain.

Prove a theorem:

```lean
CandidateSolvesFirstOrderODE solution rhs domain initialConditions
```

The claim includes residual satisfaction and initial conditions only. Existence, uniqueness, maximal interval, and full solution families require separate capabilities.

## Reification and adapters

Implement a restricted Meta reifier for:

- polynomial expressions;
- rational expressions with explicit nonzero assumptions;
- `Real.sin`;
- `Real.exp`;
- `Real.log` with positivity or nonzero domain.

Backend adapters may propose derivative syntax and a derivation tree. Lean reconstructs and checks the tree.

## Tests

- product, quotient, powers;
- nested sin/exp/log;
- missing denominator condition;
- missing log positivity;
- incorrect derivative tree;
- correct expression with incorrect derivative;
- branch/domain mismatch;
- ODE residual correct but initial condition wrong;
- completeness flag rejection;
- unsupported multivariate expression;
- theorem replay without backend.

## Integration

Collaborate with Mathlib and SciLean maintainers before stabilizing public APIs. Avoid introducing a parallel derivative ontology where existing Mathlib structures suffice.

## Acceptance

The analytic capability is complete only when checker acceptance, plus explicit domain hypotheses, directly yields `HasDerivAt`, `HasDerivWithinAt`, or the defined ODE candidate proposition for the original Lean expression.
