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
  -- Empty-row product is the empty matrix (0×p), independent of B's row count.
  if A.isEmpty then some []
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

/-- Remove row `i` and column `j` (0-based).

Uses `eraseIdx` (order-preserving) so Mathlib `ofFn` / `succAbove` transport
stays non-partial and proof-friendly (ME-RV-040).
-/
def minorRats (A : List (List ℚ)) (i j : Nat) : List (List ℚ) :=
  (A.eraseIdx i).map (·.eraseIdx j)

/-- Sign for Laplace cofactor at column `j` (0-based): `(-1)^j` as `ℚ`. -/
def laplaceSign (j : Nat) : ℚ :=
  if j % 2 = 0 then 1 else -1

/-- Closed-form determinant for sizes `n ≤ 3` (no recursion).

Matches `Matrix.det_fin_two` / `Matrix.det_fin_three`.
-/
def detRatsUpTo3 : List (List ℚ) → Option ℚ
  | [] => some 1
  | [row] =>
    if row.length = 1 then some (row.headD 0) else none
  | [r0, r1] =>
    if r0.length = 2 && r1.length = 2 then
      some (r0.getD 0 0 * r1.getD 1 0 - r0.getD 1 0 * r1.getD 0 0)
    else none
  | [r0, r1, r2] =>
    if r0.length = 3 && r1.length = 3 && r2.length = 3 then
      let a00 := r0.getD 0 0; let a01 := r0.getD 1 0; let a02 := r0.getD 2 0
      let a10 := r1.getD 0 0; let a11 := r1.getD 1 0; let a12 := r1.getD 2 0
      let a20 := r2.getD 0 0; let a21 := r2.getD 1 0; let a22 := r2.getD 2 0
      some (a00 * a11 * a22 - a00 * a12 * a21
        - a01 * a10 * a22 + a01 * a12 * a20
        + a02 * a10 * a21 - a02 * a11 * a20)
    else none
  | _ => none

/-- Explicit Fin-4 row-0 minors as 3×3 lists (avoids `minorRats` for transport proofs). -/
def fin4Minor0 (r1 r2 r3 : List ℚ) : List (List ℚ) :=
  [[r1.getD 1 0, r1.getD 2 0, r1.getD 3 0],
   [r2.getD 1 0, r2.getD 2 0, r2.getD 3 0],
   [r3.getD 1 0, r3.getD 2 0, r3.getD 3 0]]

def fin4Minor1 (r1 r2 r3 : List ℚ) : List (List ℚ) :=
  [[r1.getD 0 0, r1.getD 2 0, r1.getD 3 0],
   [r2.getD 0 0, r2.getD 2 0, r2.getD 3 0],
   [r3.getD 0 0, r3.getD 2 0, r3.getD 3 0]]

def fin4Minor2 (r1 r2 r3 : List ℚ) : List (List ℚ) :=
  [[r1.getD 0 0, r1.getD 1 0, r1.getD 3 0],
   [r2.getD 0 0, r2.getD 1 0, r2.getD 3 0],
   [r3.getD 0 0, r3.getD 1 0, r3.getD 3 0]]

def fin4Minor3 (r1 r2 r3 : List ℚ) : List (List ℚ) :=
  [[r1.getD 0 0, r1.getD 1 0, r1.getD 2 0],
   [r2.getD 0 0, r2.getD 1 0, r2.getD 2 0],
   [r3.getD 0 0, r3.getD 1 0, r3.getD 2 0]]

/-- Non-partial determinant for sizes `n ≤ 4` (Mathlib transport; ME-RV-040).

* Fin ≤ 3: `detRatsUpTo3` closed forms.
* Fin-4: Laplace along row 0 with explicit Fin-3 minors (`Matrix.det_succ_row_zero`).
-/
def detRatsSmall : List (List ℚ) → Option ℚ
  | [r0, r1, r2, r3] =>
    if r0.length = 4 && r1.length = 4 && r2.length = 4 && r3.length = 4 then
      do
        let d0 ← detRatsUpTo3 (fin4Minor0 r1 r2 r3)
        let d1 ← detRatsUpTo3 (fin4Minor1 r1 r2 r3)
        let d2 ← detRatsUpTo3 (fin4Minor2 r1 r2 r3)
        let d3 ← detRatsUpTo3 (fin4Minor3 r1 r2 r3)
        pure (r0.getD 0 0 * d0 - r0.getD 1 0 * d1 + r0.getD 2 0 * d2 - r0.getD 3 0 * d3)
    else none
  | A => detRatsUpTo3 A

/-- Sum of rational cofactor terms. -/
def sumRats (xs : List ℚ) : ℚ :=
  xs.foldl (fun acc x => acc + x) 0

/-- One Laplace cofactor term along row 0 at column `j`. -/
def laplaceCofactorTerm (d : ℚ) (row : List ℚ) (j : Nat) : ℚ :=
  laplaceSign j * row.getD j 0 * d

/-- Fuel-bounded Laplace determinant (non-`partial`, kernel-reducible).

* `fuel = 0`: only the empty matrix succeeds (`det = 1`).
* `n ≤ 4`: delegates to closed-form `detRatsSmall`.
* `n > 4`: expands along row 0, recursing on `(n-1)×(n-1)` minors with `fuel - 1`.

Call via `detRats` with `fuel = A.length`.
-/
def detRatsFuel : Nat → List (List ℚ) → Option ℚ
  | 0, A => if A.isEmpty then some 1 else none
  | fuel + 1, A =>
    if A.isEmpty then some 1
    else
      let n := A.length
      if !A.all (fun r => decide (r.length = n)) then none
      else if n ≤ 4 then detRatsSmall A
      else
        match A with
        | [] => some 1
        | row :: _ =>
          match (List.range n).mapM fun j => do
              let d ← detRatsFuel fuel (minorRats A 0 j)
              pure (laplaceCofactorTerm d row j)
          with
          | none => none
          | some terms => some (sumRats terms)

/-- Determinant via Laplace expansion along the first row (exact `ℚ`).

Non-partial fuel recursion on matrix size: `n ≤ 4` uses closed-form
`detRatsSmall`; larger square sizes expand via minors. Mathlib transport
proves `detRats (ofFnSquare A) = some A.det` for every `n` (ME-RV-040).
-/
def detRats (A : List (List ℚ)) : Option ℚ :=
  detRatsFuel A.length A

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
