/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Hypothesis.Sufficiency

namespace MathEvidence.Hypothesis

open MathEvidence.IR.RationalExpr
open MathEvidence.Checkers.RationalEquality

/-!
# Hypothesis deletion with certified justification

Remove one condition at a time. Outcomes:

* **redundant** — remaining set still passes the sufficiency checker;
* **not_redundant** — sufficiency fails; necessity remains open unless a
  certified counterexample for the weaker variant is supplied separately.

Absence of a counterexample is never treated as necessity.
-/

/-- Outcome of attempting to delete one hypothesis from a sufficient set. -/
inductive DeletionResult where
  /-- Remaining conditions still suffice (Lean checker). -/
  | redundant (remaining : List Expr)
  /-- Sufficiency fails after deletion; necessity still open. -/
  | notRedundant (remaining : List Expr)
  /-- Target condition was not in the set. -/
  | missing
  deriving DecidableEq, Repr, Inhabited

/-- Delete `target` from `conditions` (first match by `BEq`). -/
def deleteOne (conditions : List Expr) (target : Expr) : Option (List Expr) :=
  let rec go (xs : List Expr) (acc : List Expr) : Option (List Expr) :=
    match xs with
    | [] => none
    | x :: xs =>
      if x == target then some (acc.reverse ++ xs)
      else go xs (x :: acc)
  go conditions []

/-- Attempt deletion with certified redundancy justification when possible. -/
def deleteHypothesis (req : Request) (conditions : List Expr) (target : Expr) :
    DeletionResult :=
  match deleteOne conditions target with
  | none => .missing
  | some remaining =>
    if isSufficient req remaining then
      .redundant remaining
    else
      .notRedundant remaining

/-- Update lattice after a successful redundancy proof. -/
def ConditionLattice.recordRedundant
    (L : ConditionLattice) (conditionId : String) : ConditionLattice :=
  { L with
    redundant := L.redundant ++ [conditionId]
    proposed := L.proposed.map fun n =>
      if n.id = conditionId then { n with status := .redundant } else n
    originalAssumptions := L.originalAssumptions.map fun n =>
      if n.id = conditionId then { n with status := .redundant } else n
    unresolvedNecessity := L.unresolvedNecessity.filter (· ≠ conditionId) }

/-- After failed deletion without a CEX, record an open necessity question. -/
def ConditionLattice.recordUnresolvedNecessity
    (L : ConditionLattice) (conditionId : String) : ConditionLattice :=
  if L.unresolvedNecessity.contains conditionId then L
  else { L with unresolvedNecessity := L.unresolvedNecessity ++ [conditionId] }

end MathEvidence.Hypothesis
