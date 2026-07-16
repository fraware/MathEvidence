/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.RationalExpr.Eval
import MathEvidence.IR.CalculusExpr.Syntax

namespace MathEvidence.IR.CalculusExpr

open MathEvidence.IR.RationalExpr

/-!
Evaluation reuses `RationalExpr.eval`. Calculus claims are about formal
identities; pointwise evaluation is used only for documentation / IC spot checks
outside the kernel certificate path.
-/

abbrev Env (α : Type*) := MathEvidence.IR.RationalExpr.Env α

def eval {α : Type*} [Field α] [DecidableEq α] (env : Env α) (e : Expr) : Option α :=
  MathEvidence.IR.RationalExpr.eval env e

def Defined {α : Type*} [Field α] [DecidableEq α] (env : Env α) (e : Expr) : Prop :=
  MathEvidence.IR.RationalExpr.Defined env e

/-- Domain conditions hold: each listed expression is defined and nonzero. -/
def domainHolds {α : Type*} [Field α] [DecidableEq α]
    (env : Env α) (conds : List Expr) : Prop :=
  MathEvidence.IR.RationalExpr.conditionsHold env conds

end MathEvidence.IR.CalculusExpr
