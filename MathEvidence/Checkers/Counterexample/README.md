# Counterexample checker

## Claim

Establishes a **refutation** of a finite predicate at a typed witness
(Project Spec §11.3):

> `eval pred witness = some false`

## Assurance

- Mode: `kernel_replay` (Lean evaluates the original predicate).
- Backends are untrusted generators only.

## Current E2E status

The checker currently operates on MathEvidence's custom
`MathEvidence.IR.FinitePredicate` representation plus explicit finite witness
assignments. End-to-end Meta reification from arbitrary Lean predicates and
witness extraction is scaffolded in `MathEvidence.Tactic`, but it is not
implemented in this pass and must not be described as complete.

## Explicitly out of scope

- Exhaustive search
- Claims that **no** counterexample exists
- Completeness of a search campaign

Absence of a found counterexample is never treated as proof.

## Algorithm

1. Bind certificate `requestDigest` to the request digest.
2. Reject ill-formed predicates, unbounded `nat`/`int` domains, and
   out-of-domain witnesses.
3. Evaluate the predicate at the witness.
4. Accept only when evaluation yields `false`.

## Offline replay

`Replay.lean` reruns `check` with no adapter invocation.
Hand-written fixtures live in `Tests.lean` and discharge with `native_decide`.

## Axiom / `sorry` audit

- Project `sorry`: none in this checker or `IR/FinitePredicate`.
- Project-specific axioms: none.
