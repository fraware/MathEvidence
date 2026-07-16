# Product 1 — Semantic Bridge

## 1. Purpose

The Semantic Bridge converts a precisely delimited Lean expression into a solver-facing mathematical object while preserving its meaning through a Lean theorem. It is the semantic foundation of every theorem-producing MathEvidence capability.

## 2. Problem solved

Name-to-name translation is insufficient. Lean and external systems differ in types, coercions, totalization, algebraic structures, binder scope, special-function conventions, and branch semantics. A transport layer can move syntax while silently changing mathematics.

The Semantic Bridge solves this by defining small typed intermediate languages and proving that reification and executable encodings preserve the original Lean semantics.

## 3. Users

- domain checker developers;
- adapter developers;
- Lean tactic authors;
- AI agents requiring stable operation schemas;
- and library reviewers auditing end-to-end meaning.

## 4. Scope

Version 0 supports restricted exact domains:

- rational expressions;
- finite-dimensional matrices over exact coefficient fields;
- finite predicates and witnesses.

Later versions may add polynomials, algebraic numbers, optimization models, analytic expressions, tensors, and interval objects.

## 5. Non-goals

- universal Lean expression serialization;
- arbitrary Wolfram Language translation;
- automatic interpretation of unknown constants;
- implicit coercion invention;
- branch inference without user-visible conditions;
- and best-effort theorem production.

## 6. Architecture

Each domain IR includes:

1. Typed syntax.
2. Lean interpretation function.
3. Reifier from elaborated Lean expressions.
4. Proof that reification preserves evaluation.
5. Canonical variable and binder representation.
6. Canonical serialization.
7. Size and resource measures.
8. Explicit unsupported cases.
9. Backend mappings.
10. Encoding theorem for executable representations.

The bridge has no generic “foreign expression” constructor in stable mode. Experimental extensions remain outside theorem-producing modules.

## 7. Rational-expression v0

Supported constructors:

```text
variable
integer literal
rational literal
addition
subtraction
multiplication
natural power
division
negation
```

The interpreter is parameterized by a suitable field structure. The initial tactic targets `ℚ`. Generalization to abstract fields occurs only after the concrete checker is stable and the abstraction is useful to Mathlib.

Division introduces a definedness obligation. The IR records denominator subexpressions and their required nonzero conditions.

## 8. Required APIs

Lean-facing APIs:

```lean
reifyRationalExpr
interpretRationalExpr
reificationSound
collectDefinednessConditions
canonicalizeVariables
serializeRequest
```

Adapter-facing schema contains:

- operation ID;
- IR version;
- variable declarations;
- expression tree;
- assumptions;
- requested claim strength;
- resource policy;
- request digest.

## 9. Semantic invariants

- Bound and free variables cannot be confused.
- Alpha-renaming does not alter request identity after canonicalization.
- Coercions are explicit.
- Domain type is explicit.
- Every partial operation emits a definedness condition.
- Unknown Lean constants cause rejection.
- Backend mappings are versioned.
- A decoded backend expression is never assumed to be the original Lean expression; it is interpreted and checked.

## 10. Failure behavior

The bridge returns structured errors:

- unsupported expression;
- unsupported type;
- unknown constant;
- ambiguous coercion;
- unresolved type-class requirement;
- branch convention required;
- expression too large;
- or noncanonical binder.

It never silently falls back to a string translation.

## 11. Testing

- generated expression round trips;
- reification soundness examples;
- alpha-renaming;
- nested binders;
- coercion adversaries;
- division by zero cases;
- malformed serialized IR;
- and differential interpretation across backends.

## 12. Acceptance criteria

The product is stable when:

1. Two backend adapters consume one request schema.
2. Every supported constructor has a Lean semantic theorem.
3. Unsupported constructors are reliably rejected.
4. Request hashes are deterministic across platforms.
5. Expert audit finds no silent domain or coercion change in the benchmark.
6. A downstream checker proves the original Lean proposition through the bridge theorem.

## 13. Ecosystem placement

General mathematical semantics should align with Mathlib. Generic formal-language and serialization concepts may move toward CSLib after stabilization. LeanLink remains the Mathematica transport and inspection substrate, not the semantic authority.
