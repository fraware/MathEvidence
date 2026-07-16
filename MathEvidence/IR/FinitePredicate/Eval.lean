/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.FinitePredicate.Syntax

namespace MathEvidence.IR.FinitePredicate

/-- Environment: index → value. -/
abbrev Env := Nat → Option Val

def envOfAssignment (σ : Assignment) : Env :=
  fun i => σ.get? i

/-- Evaluate a term under an assignment; `none` on type errors / missing vars. -/
def evalTerm (env : Env) : Term → Option Val
  | .var i => env i
  | .lit v => some v
  | .neg t =>
    match evalTerm env t with
    | some (.int i) => some (.int (-i))
    | some (.nat n) => some (.int (-(Int.ofNat n)))
    | _ => none
  | .add a b =>
    match evalTerm env a, evalTerm env b with
    | some (.int x), some (.int y) => some (.int (x + y))
    | some (.nat x), some (.nat y) => some (.nat (x + y))
    | some (.int x), some (.nat y) => some (.int (x + Int.ofNat y))
    | some (.nat x), some (.int y) => some (.int (Int.ofNat x + y))
    | _, _ => none
  | .sub a b =>
    match evalTerm env a, evalTerm env b with
    | some (.int x), some (.int y) => some (.int (x - y))
    | some (.nat x), some (.nat y) =>
      if y ≤ x then some (.nat (x - y)) else some (.int (Int.ofNat x - Int.ofNat y))
    | some (.int x), some (.nat y) => some (.int (x - Int.ofNat y))
    | some (.nat x), some (.int y) => some (.int (Int.ofNat x - y))
    | _, _ => none
  | .mul a b =>
    match evalTerm env a, evalTerm env b with
    | some (.int x), some (.int y) => some (.int (x * y))
    | some (.nat x), some (.nat y) => some (.nat (x * y))
    | some (.int x), some (.nat y) => some (.int (x * Int.ofNat y))
    | some (.nat x), some (.int y) => some (.int (Int.ofNat x * y))
    | _, _ => none

/-- Compare values for equality (same constructor). -/
def valEq : Val → Val → Bool
  | .bool a, .bool b => decide (a = b)
  | .nat a, .nat b => decide (a = b)
  | .int a, .int b => decide (a = b)
  | .nat a, .int b => decide ((a : Int) = b)
  | .int a, .nat b => decide (a = (b : Int))
  | _, _ => false

/-- Ordered comparison for numeric values. -/
def valLe : Val → Val → Option Bool
  | .nat a, .nat b => some (decide (a ≤ b))
  | .int a, .int b => some (decide (a ≤ b))
  | .nat a, .int b => some (decide ((a : Int) ≤ b))
  | .int a, .nat b => some (decide (a ≤ (b : Int)))
  | _, _ => none

def valLt : Val → Val → Option Bool
  | .nat a, .nat b => some (decide (a < b))
  | .int a, .int b => some (decide (a < b))
  | .nat a, .int b => some (decide ((a : Int) < b))
  | .int a, .nat b => some (decide (a < (b : Int)))
  | _, _ => none

/-- Evaluate a predicate; `none` if a comparison is ill-typed. -/
def evalPred (env : Env) : Pred → Option Bool
  | .eq a b =>
    match evalTerm env a, evalTerm env b with
    | some x, some y => some (valEq x y)
    | _, _ => none
  | .ne a b =>
    match evalTerm env a, evalTerm env b with
    | some x, some y => some (!valEq x y)
    | _, _ => none
  | .le a b =>
    match evalTerm env a, evalTerm env b with
    | some x, some y => valLe x y
    | _, _ => none
  | .lt a b =>
    match evalTerm env a, evalTerm env b with
    | some x, some y => valLt x y
    | _, _ => none
  | .not p => (evalPred env p).map not
  | .and a b =>
    match evalPred env a, evalPred env b with
    | some x, some y => some (x && y)
    | _, _ => none
  | .or a b =>
    match evalPred env a, evalPred env b with
    | some x, some y => some (x || y)
    | _, _ => none

/-- Evaluate under a concrete assignment. -/
def eval (σ : Assignment) (p : Pred) : Option Bool :=
  evalPred (envOfAssignment σ) p

/-- True when the predicate evaluates to `false` at `σ` (refutation witness). -/
def isCounterexample (σ : Assignment) (p : Pred) : Bool :=
  match eval σ p with
  | some false => true
  | _ => false

end MathEvidence.IR.FinitePredicate
