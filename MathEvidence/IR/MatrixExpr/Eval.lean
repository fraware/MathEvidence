/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Data.Rat.Defs
import Mathlib.Algebra.Field.Rat
import MathEvidence.IR.MatrixExpr.Syntax

namespace MathEvidence.IR.MatrixExpr

/-- Interpret a literal as `ℚ`; `none` if denominator is zero. -/
def RatLit.toRat? (r : RatLit) : Option ℚ :=
  if r.den = 0 then none
  else some ((r.num : ℚ) / (r.den : ℚ))

/-- Rebuild a literal from `ℚ` (canonical Mathlib num/den). -/
def RatLit.ofRat (q : ℚ) : RatLit :=
  ⟨q.num, q.den⟩

/-- Evaluate a vector to rationals. -/
def evalVector? (v : Vector) : Option (List ℚ) :=
  v.mapM RatLit.toRat?

/-- Evaluate a matrix to a dense `ℚ` array. -/
def evalMatrix? (A : Matrix) : Option (List (List ℚ)) :=
  A.entries.mapM evalVector?

/-- Element-wise equality of `ℚ` matrices. -/
def ratsEqual (A B : List (List ℚ)) : Bool :=
  decide (A = B)

/-- Dot product of equal-length rational lists. -/
def dot (u v : List ℚ) : Option ℚ :=
  if u.length ≠ v.length then none
  else some (List.zip u v |>.foldl (fun acc (p : ℚ × ℚ) => acc + p.1 * p.2) 0)

/-- Matrix–matrix product over `ℚ`. -/
def mulRats (A : List (List ℚ)) (B : List (List ℚ)) : Option (List (List ℚ)) :=
  if A.isEmpty then
    if B.isEmpty then some [] else none
  else
    let k := (A.headD []).length
    let kB := B.length
    let m := (B.headD []).length
    if k ≠ kB then none
    else if !A.all (fun row => row.length = k) then none
    else if !B.all (fun row => row.length = m) then none
    else
      let colsB :=
        (List.range m).map fun j =>
          B.map fun row => row.getD j 0
      some <|
        A.map fun row =>
          colsB.map fun col =>
            (dot row col).getD 0

/-- Matrix–vector product (`A` is `n×m`, `v` length `m`). -/
def mulRatsVec (A : List (List ℚ)) (v : List ℚ) : Option (List ℚ) :=
  match mulRats A (v.map fun x => [x]) with
  | none => none
  | some M =>
    M.mapM fun row =>
      match row with
      | [x] => some x
      | _ => none

/-- Remove row `i` and column `j` (0-based). -/
def minorRats (A : List (List ℚ)) (i j : Nat) : List (List ℚ) :=
  (A.enum.filter (fun p => p.1 ≠ i)).map fun (_, row) =>
    (row.enum.filter (fun p => p.1 ≠ j)).map (·.2)

/-- Determinant via Laplace expansion along the first row (exact `ℚ`). -/
partial def detRats : List (List ℚ) → Option ℚ
  | [] => some 1
  | row :: rest =>
    let n := row.length
    if !((row :: rest).all fun r => r.length = n) then none
    else if (row :: rest).length ≠ n then none
    else if n = 0 then some 1
    else if n = 1 then some (row.headD 0)
    else
      Id.run do
        let mut acc : ℚ := 0
        for j in List.range n do
          let aij := row.getD j 0
          match detRats (minorRats (row :: rest) 0 j) with
          | none => return none
          | some d =>
            let sign : ℚ := if j % 2 = 0 then 1 else -1
            acc := acc + sign * aij * d
        return some acc

/-- Identity matrix over `ℚ`. -/
def identityRats (n : Nat) : List (List ℚ) :=
  (List.range n).map fun i =>
    (List.range n).map fun j => if i = j then (1 : ℚ) else 0

/-- Zero vector over `ℚ`. -/
def zeroRats (n : Nat) : List ℚ := List.replicate n 0

/-- True when every entry is zero. -/
def isZeroRats (v : List ℚ) : Bool :=
  v.all fun x => decide (x = 0)

/-- True when some entry is nonzero. -/
def isNonzeroRats (v : List ℚ) : Bool :=
  v.any fun x => decide (x ≠ 0)

end MathEvidence.IR.MatrixExpr
