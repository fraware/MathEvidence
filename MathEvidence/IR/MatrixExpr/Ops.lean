/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.MatrixExpr.Eval
import MathEvidence.IR.MatrixExpr.Syntax

namespace MathEvidence.IR.MatrixExpr

/-!
Executable matrix operations used by the LinearAlgebra checker.

All predicates are `Bool`-valued so offline fixtures can use `native_decide`.
-/

/-- Evaluate matrix literals; fails on zero denominators or shape mismatch. -/
def Matrix.eval? (A : Matrix) : Option (List (List ℚ)) :=
  if !A.wellFormed then none else evalMatrix? A

/-- Evaluate a vector. -/
def Vector.eval? (v : Vector) : Option (List ℚ) :=
  evalVector? v

/-- `A * B` as an evaluated `ℚ` matrix. -/
def Matrix.mulEval? (A B : Matrix) : Option (List (List ℚ)) := do
  let a ← A.eval?
  let b ← B.eval?
  mulRats a b

/-- `A * v` as an evaluated column. -/
def Matrix.mulVecEval? (A : Matrix) (v : Vector) : Option (List ℚ) := do
  let a ← A.eval?
  let x ← v.eval?
  mulRatsVec a x

/-- Determinant of a square matrix. -/
def Matrix.detEval? (A : Matrix) : Option ℚ := do
  let a ← A.eval?
  if A.nrows ≠ A.ncols then none else detRats a

/-- True when `A * B` equals the `n×n` identity. -/
def isRightInverse (A B : Matrix) : Bool :=
  match A.mulEval? B with
  | none => false
  | some M => ratsEqual M (identityRats A.nrows) && decide (A.nrows = A.ncols) &&
      decide (B.nrows = A.nrows) && decide (B.ncols = A.ncols)

/-- True when `B * A` equals the `n×n` identity. -/
def isLeftInverse (A B : Matrix) : Bool :=
  match B.mulEval? A with
  | none => false
  | some M => ratsEqual M (identityRats A.nrows) && decide (A.nrows = A.ncols) &&
      decide (B.nrows = A.nrows) && decide (B.ncols = A.ncols)

/-- Two-sided inverse witness. -/
def isInverseWitness (A B : Matrix) : Bool :=
  isRightInverse A B && isLeftInverse A B

/-- Exact linear system `A x = b`. -/
def isSystemSolution (A : Matrix) (b x : Vector) : Bool :=
  match A.mulVecEval? x, b.eval? with
  | some ax, some bv => ratsEqual (ax.map fun t => [t]) (bv.map fun t => [t]) &&
      decide (A.ncols = x.length) && decide (A.nrows = b.length)
  | _, _ => false

/-- Nontrivial kernel vector: `A v = 0` and `v ≠ 0`. -/
def isKernelVector (A : Matrix) (v : Vector) : Bool :=
  match A.mulVecEval? v with
  | none => false
  | some av =>
      isZeroRats av && isNonzeroRats (v.eval?.getD []) &&
        decide (A.ncols = v.length)

/-- Determinant identity `det A = d`. -/
def isDetIdentity (A : Matrix) (d : RatLit) : Bool :=
  match A.detEval?, d.toRat? with
  | some detA, some dq => decide (detA = dq) && decide (A.nrows = A.ncols)
  | _, _ => false

end MathEvidence.IR.MatrixExpr
