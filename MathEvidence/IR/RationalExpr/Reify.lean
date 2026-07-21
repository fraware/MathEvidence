/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.RationalExpr.Eval
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.IR.RationalExpr

/-!
# Reification

Phase 1 provides an explicit, kernel-checkable correspondence between named
rational terms and `Expr` syntax. Meta-level reification from arbitrary Lean
Expr trees is owned by `MathEvidence.Tactic` (Phase 1H) and MUST reuse these
definitions.
-/

/-- Rejection reasons for unsupported or ill-formed input (Product 01 §10). -/
inductive Reject where
  | unsupportedExpression (detail : String)
  | unsupportedType (detail : String)
  | unknownConstant (detail : String)
  | expressionTooLarge (size limit : Nat)
  | noncanonicalBinder (detail : String)
  | illFormed (detail : String)
  deriving DecidableEq, Repr, Inhabited

/-- A reified rational expression with canonical variable names. -/
structure Reified where
  varNames : List String
  expr : Expr
  deriving DecidableEq, Repr, Inhabited

/-- Default size limit for reified expressions (resource policy). -/
def defaultSizeLimit : Nat := 10000

/-- Validate well-formedness and size; return structured rejection otherwise. -/
def acceptReified (r : Reified) (sizeLimit : Nat := defaultSizeLimit) :
    Except Reject Reified :=
  let n := r.varNames.length
  if !r.expr.wellFormed n then
    .error (.illFormed "variable index or zero rat denominator")
  else if !r.expr.withinSizeLimit sizeLimit then
    .error (.expressionTooLarge r.expr.size sizeLimit)
  else if r.expr.maxVarIdx > n then
    .error (.illFormed "maxVarIdx exceeds varNames")
  else
    .ok r

/-- Build an environment from a concrete value list (missing indices → 0). -/
def envOfList {α : Type*} [Zero α] (vals : List α) : Env α :=
  fun i => vals.getD i 0

/-- Interpret a successfully accepted reification under concrete values. -/
def interpretReified {α : Type*} [Field α] [CharZero α] [DecidableEq α] (r : Reified) (vals : List α) :
    Option α :=
  eval (envOfList vals) r.expr

/-- Convenience constructors matching Product 01 supported syntax. -/
def reifyVar (names : List String) (idx : Nat) : Except Reject Reified :=
  acceptReified ⟨names, .var idx⟩

def reifyInt (names : List String) (n : Int) : Except Reject Reified :=
  acceptReified ⟨names, .int n⟩

def reifyRat (names : List String) (n : Int) (d : Nat) : Except Reject Reified :=
  if d = 0 then .error (.illFormed "rational literal denominator is zero")
  else acceptReified ⟨names, .rat n d⟩

/-- Binary combination that requires matching variable name lists. -/
def combine2 (op : Expr → Expr → Expr) (a b : Reified) : Except Reject Reified :=
  if a.varNames ≠ b.varNames then
    .error (.noncanonicalBinder "variable name lists differ")
  else
    acceptReified ⟨a.varNames, op a.expr b.expr⟩

def reifyAdd (a b : Reified) : Except Reject Reified := combine2 .add a b
def reifySub (a b : Reified) : Except Reject Reified := combine2 .sub a b
def reifyMul (a b : Reified) : Except Reject Reified := combine2 .mul a b
def reifyDiv (a b : Reified) : Except Reject Reified := combine2 .div a b

def reifyNeg (a : Reified) : Except Reject Reified :=
  acceptReified ⟨a.varNames, .neg a.expr⟩

def reifyPow (a : Reified) (k : Nat) : Except Reject Reified :=
  acceptReified ⟨a.varNames, .pow a.expr k⟩

/-- Collect definedness (denominator) conditions for a reified expression. -/
def collectDefinednessConditions (r : Reified) : List Expr :=
  r.expr.denominators

end MathEvidence.IR.RationalExpr
