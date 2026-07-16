/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.MatrixExpr.Syntax

namespace MathEvidence.IR.MatrixExpr

/-!
# Reification

Explicit constructors for exact matrix IR. Meta-level reification from Lean
matrix terms is owned by `MathEvidence.Tactic` and MUST reuse these validators.
-/

/-- Rejection reasons for unsupported or ill-formed matrix input. -/
inductive Reject where
  | unsupportedExpression (detail : String)
  | unsupportedType (detail : String)
  | illFormed (detail : String)
  | expressionTooLarge (size limit : Nat)
  | zeroDenominator
  deriving DecidableEq, Repr, Inhabited

/-- A validated matrix. -/
structure Reified where
  matrix : Matrix
  deriving DecidableEq, Repr, Inhabited

/-- Validate well-formedness and size. -/
def acceptMatrix (A : Matrix) (sizeLimit : Nat := defaultSizeLimit) :
    Except Reject Reified :=
  if A.entries.any fun row => row.any fun e => e.den = 0 then
    .error .zeroDenominator
  else if !A.wellFormed then
    .error (.illFormed "shape mismatch or ill-formed entries")
  else if !A.withinSizeLimit sizeLimit then
    .error (.expressionTooLarge A.size sizeLimit)
  else
    .ok ⟨A⟩

/-- Validate a vector of expected length. -/
def acceptVector (v : Vector) (n : Nat) : Except Reject Vector :=
  if v.any fun e => e.den = 0 then
    .error .zeroDenominator
  else if !v.wellFormed n then
    .error (.illFormed "vector length or denominator")
  else
    .ok v

/-- Convenience: integer matrix from nested `Int` lists. -/
def reifyIntMatrix (rows : List (List Int)) : Except Reject Reified :=
  let nrows := rows.length
  let ncols := (rows.headD []).length
  let A : Matrix :=
    { nrows := nrows
      ncols := ncols
      entries := rows.map fun row => row.map RatLit.ofInt }
  acceptMatrix A

/-- Convenience: integer column vector. -/
def reifyIntVector (vals : List Int) : Except Reject Vector :=
  acceptVector (vals.map RatLit.ofInt) vals.length

end MathEvidence.IR.MatrixExpr
