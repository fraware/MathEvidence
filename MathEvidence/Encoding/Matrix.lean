/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Data.List.OfFn
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Rat.Defs
import MathEvidence.IR.MatrixExpr.Eval
import MathEvidence.IR.MatrixExpr.Syntax

/-!
# Encoding — exact matrix IR

Reusable quotation lemmas: IR matrix/vector evaluation interprets as dense `ℚ`
arrays, and the Mathlib densify/quote path used by LA Meta satisfies
`densify (interpret (quote A)) = A` for `Matrix (Fin m) (Fin n) ℚ`.
-/

namespace MathEvidence.Encoding.Matrix

open MathEvidence.IR.MatrixExpr

/-- A quoted matrix interprets as a dense rational array when every entry decodes. -/
def InterpretsMatrix (quoted : Matrix) (value : List (List ℚ)) : Prop :=
  evalMatrix? quoted = some value

/-- A quoted vector interprets as a rational list when every entry decodes. -/
def InterpretsVector (quoted : Vector) (value : List ℚ) : Prop :=
  evalVector? quoted = some value

/-- Round-trip: `ofRat` then `toRat?` recovers the rational. -/
theorem ratLit_ofRat_toRat (q : ℚ) :
    RatLit.toRat? (RatLit.ofRat q) = some q := by
  simp [RatLit.ofRat, RatLit.toRat?, q.den_nz]
  exact Rat.num_div_den q

theorem ratLit_one :
    RatLit.toRat? ⟨1, 1⟩ = some 1 := by
  simp [RatLit.toRat?]

theorem ratLit_rejects_zero_den :
    RatLit.toRat? ⟨1, 0⟩ = none := by
  simp [RatLit.toRat?]

private theorem mapM_nil {a : Type*} {b : Type*} (f : a → Option b) :
    List.mapM f ([] : List a) = some [] :=
  rfl

/-- Looping `mapM` with accumulator `acc` prepends `acc.reverse` to the `acc = []` result.

Stated entirely in terms of `List.mapM.loop` so Mathlib simp lemmas that unfold
`List.mapM` cannot desynchronize the two sides of a `match`. -/
private theorem mapM_loop_eq {a : Type*} {b : Type*} (f : a → Option b)
    (as : List a) (acc : List b) :
    List.mapM.loop f as acc =
      match List.mapM.loop f as [] with
      | none => none
      | some xs => some (acc.reverse ++ xs) := by
  induction as generalizing acc with
  | nil =>
    simp [List.mapM.loop]
  | cons x as ih =>
    cases h : f x with
    | none =>
      simp [List.mapM.loop, h]
    | some y =>
      simp [List.mapM.loop, h, Option.some_bind, ih (y :: acc), ih [y]]
      cases hAs : List.mapM.loop f as [] with
      | none => rfl
      | some xs =>
        simp [List.reverse_cons, List.append_assoc]

/-- Success-preserving cons for `List.mapM`. -/
private theorem mapM_cons_some {a : Type*} {b : Type*} (f : a → Option b) (x : a) (y : b)
    (as : List a) (bs : List b)
    (ha : f x = some y) (has : List.mapM f as = some bs) :
    List.mapM f (x :: as) = some (y :: bs) := by
  simp [List.mapM, List.mapM.loop, ha]
  have h := mapM_loop_eq f as [y]
  simp [List.mapM, List.mapM.loop] at has
  simp [has] at h
  exact h

/-! ### Concrete IR lemmas (avoid general mapM.loop proofs) -/

theorem interprets_empty_matrix :
    InterpretsMatrix { nrows := 0, ncols := 0, entries := [] } [] := by
  simp only [InterpretsMatrix, evalMatrix?]
  exact mapM_nil _

theorem interprets_empty_vector :
    InterpretsVector ([] : Vector) ([] : List ℚ) := by
  simp only [InterpretsVector, evalVector?]
  exact mapM_nil _

theorem interprets_unit_vector :
    InterpretsVector [⟨1, 1⟩] [1] := by
  simp only [InterpretsVector, evalVector?]
  exact mapM_cons_some RatLit.toRat? ⟨1, 1⟩ 1 [] [] ratLit_one (mapM_nil _)

theorem interprets_singleton_vector (r : RatLit) (q : ℚ)
    (h : RatLit.toRat? r = some q) :
    InterpretsVector [r] [q] := by
  simp only [InterpretsVector, evalVector?]
  exact mapM_cons_some RatLit.toRat? r q [] [] h (mapM_nil _)

theorem interprets_vector_cons (r : RatLit) (rest : Vector) (q : ℚ) (qs : List ℚ)
    (hr : RatLit.toRat? r = some q) (hrest : InterpretsVector rest qs) :
    InterpretsVector (r :: rest) (q :: qs) := by
  simp only [InterpretsVector, evalVector?] at hrest ⊢
  exact mapM_cons_some RatLit.toRat? r q rest qs hr hrest

theorem interprets_matrix_of_rows (A : Matrix) (rows : List (List ℚ))
    (h : evalMatrix? A = some rows) :
    InterpretsMatrix A rows := h

theorem interprets_one_by_one :
    InterpretsMatrix
      { nrows := 1, ncols := 1, entries := [[⟨1, 1⟩]] }
      [[1]] := by
  simp only [InterpretsMatrix, evalMatrix?]
  exact mapM_cons_some evalVector? [⟨1, 1⟩] [1] [] [] interprets_unit_vector (mapM_nil _)

theorem interprets_matrix_rejects_zero_den :
    ¬ InterpretsMatrix
      { nrows := 1, ncols := 1, entries := [[⟨1, 0⟩]] }
      [[1]] := by
  simp only [InterpretsMatrix, evalMatrix?]
  change List.mapM.loop evalVector? [[⟨1, 0⟩]] [] ≠ some [[1]]
  have hz : evalVector? [⟨1, 0⟩] = none := by
    simp only [evalVector?, List.mapM, List.mapM.loop, ratLit_rejects_zero_den]
    rfl
  simp only [List.mapM.loop, hz]
  decide

/-! ## Mathlib densify / quote (LA Meta path) -/

/-- Quote a Mathlib column/`Fin n → ℚ` vector into exact IR. -/
def quoteVector {n : Nat} (v : Fin n → ℚ) : Vector :=
  List.ofFn fun i => RatLit.ofRat (v i)

/-- Quote a Mathlib `Matrix (Fin m) (Fin n) ℚ` into exact IR (row-major). -/
def quoteMatrix {m n : Nat} (A : _root_.Matrix (Fin m) (Fin n) ℚ) : Matrix :=
  { nrows := m
    ncols := n
    entries := List.ofFn fun i : Fin m => List.ofFn fun j : Fin n => RatLit.ofRat (A i j) }

/-- Densify a rectangular list of rationals into `Matrix (Fin m) (Fin n) ℚ`. -/
def densifyMatrix {m n : Nat} (rows : List (List ℚ)) : _root_.Matrix (Fin m) (Fin n) ℚ :=
  fun i j => (rows.getD i.val []).getD j.val 0

/-- Densify a length-`n` list into `Fin n → ℚ`. -/
def densifyVector {n : Nat} (vals : List ℚ) : Fin n → ℚ :=
  fun i => vals.getD i.val 0

private theorem evalVector_ofFn {n : Nat} (f : Fin n → ℚ) :
    evalVector? (List.ofFn fun i => RatLit.ofRat (f i)) = some (List.ofFn f) := by
  induction n with
  | zero =>
    simp only [List.ofFn_zero, evalVector?]
    exact mapM_nil _
  | succ n ih =>
    simp only [List.ofFn_succ, evalVector?]
    exact mapM_cons_some RatLit.toRat? _ _ _ _
      (ratLit_ofRat_toRat (f 0))
      (by simpa [evalVector?] using ih fun i => f i.succ)

/-- Quoted Mathlib vectors interpret as `List.ofFn`. -/
theorem interprets_quoteVector {n : Nat} (v : Fin n → ℚ) :
    InterpretsVector (quoteVector v) (List.ofFn v) := by
  simpa [InterpretsVector, quoteVector] using evalVector_ofFn v

private theorem evalMatrix_ofFn {m n : Nat} (A : _root_.Matrix (Fin m) (Fin n) ℚ) :
    evalMatrix? (quoteMatrix A) =
      some (List.ofFn fun i : Fin m => List.ofFn fun j : Fin n => A i j) := by
  induction m with
  | zero =>
    simp only [quoteMatrix, List.ofFn_zero, evalMatrix?]
    exact mapM_nil _
  | succ m ih =>
    simp only [quoteMatrix, List.ofFn_succ, evalMatrix?]
    exact mapM_cons_some evalVector? _ _ _ _
      (evalVector_ofFn fun j => A 0 j)
      (by simpa [quoteMatrix, evalMatrix?] using ih fun i j => A i.succ j)

/-- Quoted Mathlib matrices interpret as nested `List.ofFn` of entries. -/
theorem interprets_quoteMatrix {m n : Nat} (A : _root_.Matrix (Fin m) (Fin n) ℚ) :
    InterpretsMatrix (quoteMatrix A)
      (List.ofFn fun i : Fin m => List.ofFn fun j : Fin n => A i j) :=
  evalMatrix_ofFn A

private theorem getD_ofFn {α : Type*} {k : Nat} (f : Fin k → α) (i : Fin k) (d : α) :
    (List.ofFn f).getD i.val d = f i := by
  simp [List.getD_eq_getElem?_getD, List.getElem?_ofFn, List.ofFnNthVal, i.isLt]

/-- Densify recovers a Mathlib matrix from its nested `List.ofFn` entries. -/
theorem densify_ofFn {m n : Nat} (A : _root_.Matrix (Fin m) (Fin n) ℚ) :
    densifyMatrix (List.ofFn fun i : Fin m => List.ofFn fun j : Fin n => A i j) = A := by
  ext i j
  simp only [densifyMatrix]
  rw [getD_ofFn (fun i : Fin m => List.ofFn fun j : Fin n => A i j) i []]
  exact getD_ofFn (fun j : Fin n => A i j) j 0

/-- Densify recovers a Mathlib vector from `List.ofFn`. -/
theorem densifyVector_ofFn {n : Nat} (v : Fin n → ℚ) :
    densifyVector (List.ofFn v) = v := by
  funext i
  exact getD_ofFn v i 0

/-- Core LA Meta bridge: densify ∘ interpret ∘ quote = id on Mathlib matrices. -/
theorem densify_interpret_quote {m n : Nat} (A : _root_.Matrix (Fin m) (Fin n) ℚ) :
    densifyMatrix ((evalMatrix? (quoteMatrix A)).getD []) = A := by
  rw [evalMatrix_ofFn, Option.getD_some, densify_ofFn]

/-- Vector form of densify ∘ interpret ∘ quote. -/
theorem densifyVector_interpret_quote {n : Nat} (v : Fin n → ℚ) :
    densifyVector ((evalVector? (quoteVector v)).getD []) = v := by
  simp only [quoteVector]
  rw [evalVector_ofFn, Option.getD_some, densifyVector_ofFn]

/-- Concrete 2×2 identity used by LA examples. -/
theorem densify_interpret_quote_I2 :
    let I2 : _root_.Matrix (Fin 2) (Fin 2) ℚ := fun i j => if i = j then 1 else 0
    densifyMatrix ((evalMatrix? (quoteMatrix I2)).getD []) = I2 :=
  densify_interpret_quote _

end MathEvidence.Encoding.Matrix
