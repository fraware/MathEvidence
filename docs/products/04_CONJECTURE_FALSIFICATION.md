# Product 4 — Conjecture and Falsification Engine

## 1. Purpose

This product supports disciplined computational discovery over formally defined mathematical object families. It generates examples and invariants, proposes candidate conjectures, actively searches for counterexamples, certifies refutations in Lean, and forwards surviving statements to proof systems.

## 2. Problem solved

Most formal theorem-proving systems begin from a fixed proposition. Research mathematics often requires discovering the proposition itself. Computational systems are strong at finite exploration and invariant computation, while Lean provides precise object definitions and certified conclusions.

## 3. Workflow

```text
Lean object family
→ executable instance generator
→ backend invariant computation
→ pattern proposal
→ Lean statement generation
→ counterexample campaign
→ Lean-certified refutation or surviving conjecture
→ proof attempt and library integration
```

## 4. Object-family contract

A domain integration defines:

- formal object type;
- bounded generator or enumerator;
- isomorphism or duplicate policy;
- computable invariants;
- admissibility conditions;
- and a theorem connecting generated executable objects to formal objects.

## 5. Conjecture states

- `observed_pattern`
- `candidate_statement`
- `falsified`
- `bounded_verified`
- `formally_proved`
- `open`

Bounded verification is never presented as a theorem over the unbounded family.

## 6. Initial domains

- finite graphs;
- finite algebraic structures;
- integer sequences and recurrences;
- small matrix families;
- and finite counterexamples to generated algebraic statements.

## 7. Falsification policy

Counterexample search is mandatory before expensive proof search unless the domain integration opts out with justification. Search campaigns record bounds, generators, backend versions, and coverage.

A returned counterexample changes status only after Lean verifies:

- witness admissibility;
- interpretation correctness;
- and failure of the original proposition.

## 8. AI role

AI models may:

- select invariants;
- propose generalizations;
- prioritize search regions;
- and explain patterns.

They do not determine proof status.

## 9. Data outputs

Every episode records positive examples, near misses, false variants, certified counterexamples, statement revisions, and final proof status. This is intended to train theory-formation systems, not only theorem completers.

## 10. Failure modes

- trivial pattern generation;
- duplicate isomorphic examples;
- data leakage from known theorems;
- finite evidence presented as universal;
- invariant computation inconsistent with Lean definitions;
- and excessive production of low-value conjectures.

## 11. Acceptance criteria

1. At least one domain family has a verified executable encoding.
2. Certified counterexamples reliably refute false candidates.
3. The system clearly separates bounded evidence from proof.
4. Expert review finds a useful precision rate among proposed conjectures.
5. At least one surviving conjecture produces a reusable theorem or meaningful open problem.
