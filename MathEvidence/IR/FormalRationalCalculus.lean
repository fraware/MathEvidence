/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.CalculusExpr.Syntax
import MathEvidence.IR.CalculusExpr.Ops
import MathEvidence.IR.CalculusExpr.Eval
import MathEvidence.IR.CalculusExpr.Serialize
import MathEvidence.IR.CalculusExpr.Soundness
import MathEvidence.IR.CalculusExpr.Reify

namespace MathEvidence.IR.FormalRationalCalculus

/-!
# FormalRationalCalculus

Additive alias barrel for `MathEvidence.IR.CalculusExpr` during the
PR-Calculus-Reclassification transition.

This capability is formal rational calculus: syntactic differentiation,
substitution, recurrence, and ODE-candidate identities over the restricted
rational-expression fragment. It does not claim Mathlib analytic derivative,
continuity, ODE existence/uniqueness, or equality at poles.
-/

abbrev Expr := MathEvidence.IR.RationalExpr.Expr
abbrev Env (α : Type*) := MathEvidence.IR.CalculusExpr.Env α
abbrev Operation := MathEvidence.IR.CalculusExpr.Operation
abbrev InitialCondition := MathEvidence.IR.CalculusExpr.InitialCondition

abbrev defaultSizeLimit : Nat := MathEvidence.IR.CalculusExpr.defaultSizeLimit
def densCovered (e : Expr) (conds : List Expr) : Bool :=
  MathEvidence.IR.CalculusExpr.densCovered e conds

def exprsWithinLimit (es : List Expr) (limit : Nat := defaultSizeLimit) : Bool :=
  MathEvidence.IR.CalculusExpr.exprsWithinLimit es limit

def eval {α : Type*} [Field α] [CharZero α] [DecidableEq α] (env : Env α) (e : Expr) :
    Option α :=
  MathEvidence.IR.CalculusExpr.eval env e

def Defined {α : Type*} [Field α] [CharZero α] [DecidableEq α] (env : Env α) (e : Expr) :
    Prop :=
  MathEvidence.IR.CalculusExpr.Defined env e

def domainHolds {α : Type*} [Field α] [CharZero α] [DecidableEq α]
    (env : Env α) (conds : List Expr) : Prop :=
  MathEvidence.IR.CalculusExpr.domainHolds env conds

end MathEvidence.IR.FormalRationalCalculus
