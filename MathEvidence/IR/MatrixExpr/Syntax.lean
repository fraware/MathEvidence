/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.IR.MatrixExpr

/-- Exact rational literal `num / den` with explicit nonnegative denominator. -/
structure RatLit where
  num : Int
  den : Nat := 1
  deriving DecidableEq, Repr, Inhabited

/-- Integer embedding. -/
def RatLit.ofInt (n : Int) : RatLit := ⟨n, 1⟩

/-- Column vector of rational literals. -/
abbrev Vector := List RatLit

/-- Dense rectangular matrix over exact rationals (row-major).

Dimensions are explicit; `entries` MUST have length `nrows` and each row length
`ncols` when well-formed. -/
structure Matrix where
  nrows : Nat
  ncols : Nat
  entries : List Vector
  deriving DecidableEq, Repr, Inhabited

/-- Exact custom matrix IR used by MathEvidence linear-algebra checkers.

This is intentionally an alias for this namespace's `Matrix`, not mathlib's
`Matrix (Fin m) (Fin n) ℚ`. Tactic-level Meta reification should target
mathlib matrices and then lower into this exact IR through validators. -/
abbrev ExactMatrixIR := Matrix

/-- Number of scalar entries (resource measure). -/
def Matrix.size (A : Matrix) : Nat :=
  A.nrows * A.ncols

/-- Structural size including nested list overhead. -/
def Matrix.entryCount (A : Matrix) : Nat :=
  A.entries.foldl (fun acc row => acc + row.length) 0

/-- Default hard size limit (entries). -/
def defaultSizeLimit : Nat := 64

/-- True when every literal has nonzero denominator and shape matches dims. -/
def Matrix.wellFormed (A : Matrix) : Bool :=
  decide (A.entries.length = A.nrows) &&
    A.entries.all fun row =>
      decide (row.length = A.ncols) &&
        row.all fun e => decide (e.den ≠ 0)

/-- Vector length matches `n` and all dens nonzero. -/
def Vector.wellFormed (v : Vector) (n : Nat) : Bool :=
  decide (v.length = n) && v.all fun e => decide (e.den ≠ 0)

/-- Reject oversized matrices. -/
def Matrix.withinSizeLimit (A : Matrix) (limit : Nat := defaultSizeLimit) : Bool :=
  decide (A.size ≤ limit) && decide (A.entryCount ≤ limit)

/-- Square identity matrix of size `n` with 1 on the diagonal. -/
def Matrix.identity (n : Nat) : Matrix :=
  { nrows := n
    ncols := n
    entries :=
      (List.range n).map fun i =>
        (List.range n).map fun j =>
          if i = j then RatLit.ofInt 1 else RatLit.ofInt 0 }

/-- Zero matrix. -/
def Matrix.zero (r c : Nat) : Matrix :=
  { nrows := r
    ncols := c
    entries := List.replicate r (List.replicate c (RatLit.ofInt 0)) }

/-- Zero vector of length `n`. -/
def Vector.zero (n : Nat) : Vector :=
  List.replicate n (RatLit.ofInt 0)

/-- Column matrix from a vector. -/
def Matrix.ofCol (v : Vector) : Matrix :=
  { nrows := v.length
    ncols := 1
    entries := v.map fun x => [x] }

/-- Row matrix from a vector. -/
def Matrix.ofRow (v : Vector) : Matrix :=
  { nrows := 1
    ncols := v.length
    entries := [v] }

/-- Extract the single column of an `n×1` matrix as a vector. -/
def Matrix.toCol? (A : Matrix) : Option Vector :=
  if A.ncols ≠ 1 then none
  else
    let col := A.entries.map fun row => row.headD (RatLit.ofInt 0)
    if col.length = A.nrows then some col else none

end MathEvidence.IR.MatrixExpr
