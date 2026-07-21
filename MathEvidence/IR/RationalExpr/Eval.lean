/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.Field.Basic
import Mathlib.Algebra.Field.Rat
import Mathlib.Data.Rat.Defs
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.IR.RationalExpr

/-- Environment mapping variable indices to field elements. -/
abbrev Env (α : Type*) := Nat → α

/--
Partial evaluation. For `rat` literals, reject both a zero natural denominator and
a denominator whose cast vanishes; the latter avoids a positive-characteristic
footgun when evaluating outside `ℚ`.
-/
def eval {α : Type*} [Field α] [CharZero α] [DecidableEq α] (env : Env α) : Expr → Option α
  | .var i => some (env i)
  | .int n => some (n : α)
  | .rat n d =>
    if d = 0 then none
    else if (d : α) = 0 then none
    else some ((n : α) / (d : α))
  | .neg e => (eval env e).map (fun v => -v)
  | .add a b => do
    let x ← eval env a
    let y ← eval env b
    pure (x + y)
  | .sub a b => do
    let x ← eval env a
    let y ← eval env b
    pure (x - y)
  | .mul a b => do
    let x ← eval env a
    let y ← eval env b
    pure (x * y)
  | .pow b k => (eval env b).map (fun v => v ^ k)
  | .div n d => do
    let x ← eval env n
    let y ← eval env d
    if y = 0 then none else pure (x / y)

/-- Definedness as a proposition (matches `eval`). -/
def Defined {α : Type*} [Field α] [CharZero α] [DecidableEq α] (env : Env α) : Expr → Prop
  | .var _ => True
  | .int _ => True
  | .rat _ d => d ≠ 0 ∧ (d : α) ≠ 0
  | .neg e => Defined env e
  | .add a b | .sub a b | .mul a b => Defined env a ∧ Defined env b
  | .pow b _ => Defined env b
  | .div n d => Defined env n ∧ Defined env d ∧ eval env d ≠ some 0

/-- Total evaluation under a definedness proof. -/
noncomputable def evalDefined {α : Type*} [Field α] [CharZero α] [DecidableEq α] (env : Env α) :
    (e : Expr) → Defined env e → α
  | .var i, _ => env i
  | .int n, _ => (n : α)
  | .rat n d, h =>
    have : d ≠ 0 := h.1
    (n : α) / (d : α)
  | .neg e, h => -(evalDefined env e h)
  | .add a b, h => evalDefined env a h.1 + evalDefined env b h.2
  | .sub a b, h => evalDefined env a h.1 - evalDefined env b h.2
  | .mul a b, h => evalDefined env a h.1 * evalDefined env b h.2
  | .pow b k, h => (evalDefined env b h) ^ k
  | .div n d, h =>
    evalDefined env n h.1 / evalDefined env d h.2.1

/-- Specialization to `ℚ`. -/
abbrev evalℚ (env : Env ℚ) (e : Expr) : Option ℚ := eval (α := ℚ) env e

/-- All listed conditions evaluate to a nonzero value. -/
def conditionsHold {α : Type*} [Field α] [CharZero α] [DecidableEq α] (env : Env α) (conds : List Expr) :
    Prop :=
  ∀ c ∈ conds, ∃ v, eval env c = some v ∧ v ≠ 0

/-- Executable check that every condition is defined and nonzero. -/
def conditionsHoldDec {α : Type*} [Field α] [CharZero α] [DecidableEq α]
    (env : Env α) (conds : List Expr) : Bool :=
  conds.all fun c =>
    match eval env c with
    | some v => decide (v ≠ 0)
    | none => false

end MathEvidence.IR.RationalExpr
