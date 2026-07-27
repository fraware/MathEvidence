/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Algebra.BigOperators.Group.Finset
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.LinearAlgebra.Matrix.Determinant.Basic
import Mathlib.Tactic.Abel
import Mathlib.Tactic.Ring
import MathEvidence.Checkers.LinearAlgebra.Soundness
import MathEvidence.Encoding.Matrix
import MathEvidence.IR.MatrixExpr.Ops
import MathEvidence.IR.MatrixExpr.Soundness
import MathEvidence.Checkers.LinearAlgebra.BridgeDet

/-!
# Linear-algebra Mathlib bridge (ME-RV-040)

Transport theorems from IR Bool checkers plus
`densify ∘ interpret ∘ quote = id` into ordinary Mathlib matrix goals.

Proof authority is IR soundness (`isRightInverse_sound`, …) applied to
quoted matrices, transported by densify / `mulRats` lemmas.

Completed: inverse family via `mulRats_ofFn_square` (general square `n`);
system / kernel via general rectangular `mulRatsVec_ofFn` (any `m×n`);
det Mathlib transport for all square `Fin n` via non-partial fuel
`detRats` (`detRatsSmall` ≤ 4; Laplace + `det_succ_row_zero` for `n > 4`).
-/

namespace MathEvidence.Checkers.LinearAlgebra.Bridge

open Matrix
open MathEvidence.IR.MatrixExpr
open MathEvidence.Encoding.Matrix
open MathEvidence.Checkers.LinearAlgebra

/-- Quoted IR of a Mathlib matrix equals the Meta-reified IR matrix. -/
def QuotesMatrix {m n : Nat} (A : _root_.Matrix (Fin m) (Fin n) ℚ) (ir : Matrix) :
    Prop :=
  quoteMatrix A = ir

/-- Quoted IR of a Mathlib vector equals the Meta-reified IR vector. -/
def QuotesVector {k : Nat} (v : Fin k → ℚ) (ir : Vector) : Prop :=
  quoteVector v = ir

/-- Package: `checkBool` acceptance implies the IR claim proposition. -/
theorem checkBool_implies_proposition
    (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) :
    Claim.proposition req.claim cert.inverse cert.vector :=
  checkBool_sound req cert h

/-- Quoted matrices are well-formed. -/
theorem quoteMatrix_wellFormed {m n : Nat}
    (A : _root_.Matrix (Fin m) (Fin n) ℚ) :
    (quoteMatrix A).wellFormed = true := by
  simp only [quoteMatrix, Matrix.wellFormed, List.length_ofFn, decide_True, Bool.true_and,
    List.all_eq_true]
  intro row hr
  rw [List.mem_ofFn] at hr
  obtain ⟨i, rfl⟩ := hr
  simp only [List.length_ofFn, decide_True, Bool.true_and, List.all_eq_true]
  intro e he
  rw [List.mem_ofFn] at he
  obtain ⟨j, rfl⟩ := he
  simpa [RatLit.ofRat, decide_eq_true_eq] using Rat.den_nz (A i j)

/-- `Matrix.eval?` of a quote recovers nested `List.ofFn` entries. -/
theorem quoteMatrix_eval? {m n : Nat}
    (A : _root_.Matrix (Fin m) (Fin n) ℚ) :
    (quoteMatrix A).eval? =
      some (List.ofFn fun i : Fin m => List.ofFn fun j : Fin n => A i j) := by
  simp only [Matrix.eval?, quoteMatrix_wellFormed, Bool.not_true]
  exact interprets_quoteMatrix A

private theorem foldl_zip_ofFn {n : Nat} (c : ℚ) (f g : Fin n → ℚ) :
    (List.zip (List.ofFn f) (List.ofFn g)).foldl
        (fun acc (p : ℚ × ℚ) => acc + p.1 * p.2) c =
      c + ∑ k : Fin n, f k * g k := by
  induction n generalizing c with
  | zero => simp [List.ofFn_zero]
  | succ n ih =>
    simp only [List.ofFn_succ, List.zip_cons_cons, List.foldl_cons]
    rw [ih, Fin.sum_univ_succ]
    abel

private theorem dot_ofFn {n : Nat} (f g : Fin n → ℚ) :
    dot (List.ofFn f) (List.ofFn g) = some (∑ k : Fin n, f k * g k) := by
  simp [dot, List.length_ofFn, foldl_zip_ofFn]

private theorem map_getD_ofFn_col {n p : Nat}
    (B : _root_.Matrix (Fin n) (Fin p) ℚ) (j : Fin p) :
    (List.ofFn fun i : Fin n => List.ofFn fun j' : Fin p => B i j').map
        (fun row => row.getD j.val 0) =
      List.ofFn fun i : Fin n => B i j := by
  refine List.ext_getElem (by simp [List.length_map, List.length_ofFn]) ?_
  intro i hi _
  have : i < n := by simpa [List.length_ofFn, List.length_map] using hi
  simp [List.getElem_map, List.getElem_ofFn, List.getD_eq_getElem?_getD,
    List.getElem?_ofFn, j.isLt]

/-- Columns of an `ofFn` matrix, as used by `mulRats`. -/
private theorem colsB_ofFn {k p : Nat}
    (B : _root_.Matrix (Fin k) (Fin p) ℚ) :
    (List.range p).map (fun j =>
        (List.ofFn fun i : Fin k => List.ofFn fun j' : Fin p => B i j').map
          (fun row => row.getD j 0)) =
      List.ofFn fun j : Fin p => List.ofFn fun i : Fin k => B i j := by
  refine List.ext_getElem (by simp [List.length_map, List.length_range, List.length_ofFn]) ?_
  intro j hj hj'
  have hjFin : j < p := by simpa [List.length_map, List.length_range] using hj
  simp only [List.getElem_map, List.getElem_range, List.getElem_ofFn]
  exact map_getD_ofFn_col B ⟨j, hjFin⟩

/-- Columns of an `ofFn` square matrix (inverse bridges). -/
private theorem colsB_ofFn_square {n : Nat}
    (B : _root_.Matrix (Fin n) (Fin n) ℚ) :
    (List.range n).map (fun j =>
        (List.ofFn fun i : Fin n => List.ofFn fun j' : Fin n => B i j').map
          (fun row => row.getD j 0)) =
      List.ofFn fun j : Fin n => List.ofFn fun i : Fin n => B i j :=
  colsB_ofFn B

/-- One `mulRats` cell equals the Mathlib product entry (rectangular). -/
private theorem mulRats_cell_ofFn {m k p : Nat}
    (A : _root_.Matrix (Fin m) (Fin k) ℚ) (B : _root_.Matrix (Fin k) (Fin p) ℚ)
    (i : Fin m) (j : Fin p) :
    (dot (List.ofFn fun t : Fin k => A i t)
        (List.ofFn fun t : Fin k => B t j)).getD 0 =
      (A * B) i j := by
  rw [dot_ofFn, Option.getD_some, Matrix.mul_apply]

/-- Square-case `mulRats` (sufficient for inverse bridges). -/
theorem mulRats_ofFn_square {n : Nat}
    (A B : _root_.Matrix (Fin n) (Fin n) ℚ) :
    mulRats (List.ofFn fun i : Fin n => List.ofFn fun j : Fin n => A i j)
        (List.ofFn fun i : Fin n => List.ofFn fun j : Fin n => B i j) =
      some (List.ofFn fun i : Fin n => List.ofFn fun j : Fin n => (A * B) i j) := by
  cases n with
  | zero =>
    simp [mulRats, List.ofFn_zero]
  | succ n =>
    let A' := List.ofFn fun i : Fin (n + 1) => List.ofFn fun j : Fin (n + 1) => A i j
    let B' := List.ofFn fun i : Fin (n + 1) => List.ofFn fun j : Fin (n + 1) => B i j
    have hAempty : A'.isEmpty = false := by
      simp [A', List.ofFn_succ]
    have hhead : (A'.headD []).length = n + 1 := by
      simp [A', List.ofFn_succ, List.length_ofFn]
    have hBlen : B'.length = n + 1 := by
      simp [B', List.length_ofFn]
    have hBhead : (B'.headD []).length = n + 1 := by
      simp [B', List.ofFn_succ, List.length_ofFn]
    have hAall : A'.all (fun row => decide (row.length = n + 1)) = true := by
      change (List.ofFn fun i : Fin (n + 1) =>
          List.ofFn fun j : Fin (n + 1) => A i j).all
          (fun row => decide (row.length = n + 1)) = true
      refine (List.all_eq_true).2 ?_
      intro row hr
      rw [List.mem_ofFn, Set.mem_range] at hr
      obtain ⟨i, rfl⟩ := hr
      simp [List.length_ofFn]
    have hBall : B'.all (fun row => decide (row.length = n + 1)) = true := by
      change (List.ofFn fun i : Fin (n + 1) =>
          List.ofFn fun j : Fin (n + 1) => B i j).all
          (fun row => decide (row.length = n + 1)) = true
      refine (List.all_eq_true).2 ?_
      intro row hr
      rw [List.mem_ofFn, Set.mem_range] at hr
      obtain ⟨i, rfl⟩ := hr
      simp [List.length_ofFn]
    have hmul :
        mulRats A' B' =
          some (List.ofFn fun i : Fin (n + 1) =>
            List.ofFn fun j : Fin (n + 1) => (A * B) i j) := by
      unfold mulRats
      simp only [hAempty, ↓reduceIte, hhead, hBlen, hBhead, ne_eq, not_true_eq_false,
        ↓reduceIte, hAall, hBall, Bool.not_true, Bool.false_eq_true, ↓reduceIte]
      refine congrArg some ?_
      have hcols :
          (List.range (n + 1)).map (fun j => B'.map fun row => row.getD j 0) =
            List.ofFn fun j : Fin (n + 1) => List.ofFn fun i : Fin (n + 1) => B i j := by
        simpa [B'] using colsB_ofFn_square B
      rw [hcols, show A' = List.ofFn fun i : Fin (n + 1) =>
          List.ofFn fun j : Fin (n + 1) => A i j from rfl]
      simp only [List.map_ofFn]
      congr 1
      funext i
      simp only [Function.comp_apply, List.map_ofFn]
      congr 1
      funext j
      simp only [Function.comp_apply]
      exact mulRats_cell_ofFn A B i j
    simpa [A', B'] using hmul

/-- Right-inverse IR acceptance on quotes ⇒ Mathlib `A * B = 1`. -/
theorem right_inverse_of_isRightInverse {n : Nat}
    (A B : _root_.Matrix (Fin n) (Fin n) ℚ)
    (h : isRightInverse (quoteMatrix A) (quoteMatrix B) = true) :
    A * B = 1 := by
  obtain ⟨M, hMul, hId⟩ := isRightInverse_sound (quoteMatrix A) (quoteMatrix B) h
  have hAq := quoteMatrix_eval? A
  have hBq := quoteMatrix_eval? B
  have hmulRats :
      mulRats (List.ofFn fun i : Fin n => List.ofFn fun j : Fin n => A i j)
          (List.ofFn fun i : Fin n => List.ofFn fun j : Fin n => B i j) = some M := by
    simpa [Matrix.mulEval?, hAq, hBq] using hMul
  have hM :
      M = List.ofFn fun i : Fin n => List.ofFn fun j : Fin n => (A * B) i j :=
    Option.some.inj (hmulRats.symm.trans (mulRats_ofFn_square A B))
  have hr : (quoteMatrix A).nrows = n := rfl
  rw [hr] at hId
  have hdensify_prod : densifyMatrix M = A * B := by
    rw [hM, densify_ofFn]
  have hdensify_id : densifyMatrix M = (1 : _root_.Matrix (Fin n) (Fin n) ℚ) := by
    rw [hId, densify_identityRats]
  exact hdensify_prod.symm.trans hdensify_id

/-- Two-sided inverse from IR `isInverseWitness`. -/
theorem inverse_of_isInverseWitness {n : Nat}
    (A B : _root_.Matrix (Fin n) (Fin n) ℚ)
    (h : isInverseWitness (quoteMatrix A) (quoteMatrix B) = true) :
    A * B = 1 ∧ B * A = 1 := by
  simp only [isInverseWitness, Bool.and_eq_true] at h
  exact ⟨right_inverse_of_isRightInverse A B h.1,
    right_inverse_of_isRightInverse B A h.2⟩

/-! ## Matrix–vector / system / kernel (general rectangular) + det (general-n) -/

private theorem quoteVector_eval? {k : Nat} (v : Fin k → ℚ) :
    (quoteVector v).eval? = some (List.ofFn v) :=
  interprets_quoteVector v

/-- Column matrix of a vector (reduces `mulRatsVec` to `mulRats`). -/
private def colMatrix {n : Nat} (v : Fin n → ℚ) : _root_.Matrix (Fin n) (Fin 1) ℚ :=
  fun i _ => v i

private theorem colMatrix_entries {n : Nat} (v : Fin n → ℚ) :
    (List.ofFn fun i : Fin n => List.ofFn fun _j : Fin 1 => colMatrix v i ⟨0, by decide⟩) =
      (List.ofFn v).map fun x => [x] := by
  refine List.ext_getElem (by simp [List.length_ofFn, List.length_map]) ?_
  intro i hi _
  have : i < n := by simpa [List.length_ofFn] using hi
  simp [List.getElem_ofFn, List.getElem_map, colMatrix, List.ofFn_succ, List.ofFn_zero]

/-- Rectangular `mulRats` recovers Mathlib matrix product.

Requires `k ≠ 0` because IR `mulRats` reads column count from `B.headD`, which
is `0` when `B` is empty (unlike Mathlib's `m×p` zero product for `k = 0`). -/
theorem mulRats_ofFn {m k p : Nat} [NeZero k]
    (A : _root_.Matrix (Fin m) (Fin k) ℚ) (B : _root_.Matrix (Fin k) (Fin p) ℚ) :
    mulRats (List.ofFn fun i : Fin m => List.ofFn fun j : Fin k => A i j)
        (List.ofFn fun i : Fin k => List.ofFn fun j : Fin p => B i j) =
      some (List.ofFn fun i : Fin m => List.ofFn fun j : Fin p => (A * B) i j) := by
  cases m with
  | zero =>
    simp [mulRats, List.ofFn_zero]
  | succ m =>
    let A' := List.ofFn fun i : Fin (m + 1) => List.ofFn fun j : Fin k => A i j
    let B' := List.ofFn fun i : Fin k => List.ofFn fun j : Fin p => B i j
    have hAempty : A'.isEmpty = false := by
      simp [A', List.ofFn_succ]
    have hhead : (A'.headD []).length = k := by
      simp [A', List.ofFn_succ, List.length_ofFn]
    have hBlen : B'.length = k := by
      simp [B', List.length_ofFn]
    have hBhead : (B'.headD []).length = p := by
      obtain ⟨k', rfl⟩ := Nat.exists_eq_succ_of_ne_zero (NeZero.ne k)
      simp [B', List.ofFn_succ, List.length_ofFn]
    have hAall : A'.all (fun row => decide (row.length = k)) = true := by
      change (List.ofFn fun i : Fin (m + 1) =>
          List.ofFn fun j : Fin k => A i j).all
          (fun row => decide (row.length = k)) = true
      refine (List.all_eq_true).2 ?_
      intro row hr
      rw [List.mem_ofFn, Set.mem_range] at hr
      obtain ⟨i, rfl⟩ := hr
      simp [List.length_ofFn]
    have hBall : B'.all (fun row => decide (row.length = p)) = true := by
      change (List.ofFn fun i : Fin k =>
          List.ofFn fun j : Fin p => B i j).all
          (fun row => decide (row.length = p)) = true
      refine (List.all_eq_true).2 ?_
      intro row hr
      rw [List.mem_ofFn, Set.mem_range] at hr
      obtain ⟨i, rfl⟩ := hr
      simp [List.length_ofFn]
    have hmul :
        mulRats A' B' =
          some (List.ofFn fun i : Fin (m + 1) =>
            List.ofFn fun j : Fin p => (A * B) i j) := by
      unfold mulRats
      simp only [hAempty, ↓reduceIte, hhead, hBlen, hBhead, ne_eq, not_true_eq_false,
        ↓reduceIte, hAall, hBall, Bool.not_true, Bool.false_eq_true, ↓reduceIte]
      refine congrArg some ?_
      have hcols :
          (List.range p).map (fun j => B'.map fun row => row.getD j 0) =
            List.ofFn fun j : Fin p => List.ofFn fun i : Fin k => B i j := by
        simpa [B'] using colsB_ofFn B
      rw [hcols, show A' = List.ofFn fun i : Fin (m + 1) =>
          List.ofFn fun j : Fin k => A i j from rfl]
      simp only [List.map_ofFn]
      congr 1
      funext i
      simp only [Function.comp_apply, List.map_ofFn]
      congr 1
      funext j
      simp only [Function.comp_apply]
      exact mulRats_cell_ofFn A B i j
    simpa [A', B'] using hmul

private def extractSingleton : List ℚ → Option ℚ
  | [x] => some x
  | _ => none

private theorem mapM_singleton_col {m : Nat} (f : Fin m → ℚ) :
    (List.ofFn fun i : Fin m => ([f i] : List ℚ)).mapM extractSingleton =
      some (List.ofFn f) := by
  induction m with
  | zero =>
    rw [List.ofFn_zero, List.mapM_nil]
    rfl
  | succ m ih =>
    rw [List.ofFn_succ, List.mapM_cons, show extractSingleton [f 0] = some (f 0) from rfl,
      ih (fun i : Fin m => f i.succ)]
    simp [Option.bind, List.ofFn_succ]

/-- General rectangular matrix–vector: IR `mulRatsVec` recovers Mathlib `mulVec`.

`NeZero n` excludes the empty-column IR edge case (`mulRats` headD quirk). -/
theorem mulRatsVec_ofFn {m n : Nat} [NeZero n]
    (A : _root_.Matrix (Fin m) (Fin n) ℚ) (v : Fin n → ℚ) :
    mulRatsVec (List.ofFn fun i : Fin m => List.ofFn fun j : Fin n => A i j)
        (List.ofFn v) =
      some (List.ofFn (A.mulVec v)) := by
  have hmul := mulRats_ofFn A (colMatrix v)
  have hcol := colMatrix_entries v
  have hprod :
      List.ofFn (fun i : Fin m => List.ofFn fun j : Fin 1 => (A * colMatrix v) i j) =
        List.ofFn fun i : Fin m => ([(A.mulVec v) i] : List ℚ) := by
    refine List.ext_getElem (by simp [List.length_ofFn]) ?_
    intro i hi _
    have : i < m := by simpa [List.length_ofFn] using hi
    simp [List.getElem_ofFn, List.ofFn_succ, List.ofFn_zero, Matrix.mul_apply,
      Matrix.mulVec, colMatrix, dotProduct]
  unfold mulRatsVec
  have hA :
      mulRats (List.ofFn fun i : Fin m => List.ofFn fun j : Fin n => A i j)
          ((List.ofFn v).map fun x => [x]) =
        some (List.ofFn fun i : Fin m => ([(A.mulVec v) i] : List ℚ)) := by
    rw [← hcol]
    exact hmul.trans (congrArg some hprod)
  simp only [hA, Option.bind]
  exact mapM_singleton_col (A.mulVec v)

theorem mulRatsVec_ofFn_fin2
    (A : _root_.Matrix (Fin 2) (Fin 2) ℚ) (v : Fin 2 → ℚ) :
    mulRatsVec (List.ofFn fun i : Fin 2 => List.ofFn fun j : Fin 2 => A i j)
        (List.ofFn v) =
      some (List.ofFn (A.mulVec v)) :=
  mulRatsVec_ofFn A v

theorem mulRatsVec_ofFn_fin3
    (A : _root_.Matrix (Fin 3) (Fin 3) ℚ) (v : Fin 3 → ℚ) :
    mulRatsVec (List.ofFn fun i : Fin 3 => List.ofFn fun j : Fin 3 => A i j)
        (List.ofFn v) =
      some (List.ofFn (A.mulVec v)) :=
  mulRatsVec_ofFn A v

private theorem isZeroRats_ofFn {n : Nat} (v : Fin n → ℚ) :
    isZeroRats (List.ofFn v) = true ↔ v = 0 := by
  simp only [isZeroRats, List.all_eq_true, decide_eq_true_eq, funext_iff,
    List.mem_ofFn, Set.mem_range]
  constructor
  · intro h i
    exact h (v i) ⟨i, rfl⟩
  · intro h x hx
    obtain ⟨i, rfl⟩ := hx
    exact h i

private theorem isNonzeroRats_ofFn {n : Nat} (v : Fin n → ℚ) :
    isNonzeroRats (List.ofFn v) = true ↔ v ≠ 0 := by
  constructor
  · intro h hv
    simp only [isNonzeroRats, List.any_eq_true, decide_eq_true_eq, hv, Pi.zero_apply,
      List.mem_ofFn, Set.mem_range] at h
    obtain ⟨x, ⟨i, rfl⟩, hne⟩ := h
    exact hne rfl
  · intro h
    simp only [isNonzeroRats, List.any_eq_true, decide_eq_true_eq, List.mem_ofFn,
      Set.mem_range]
    by_contra hany
    push_neg at hany
    have hz : v = 0 := by
      funext i
      exact hany (v i) ⟨i, rfl⟩
    exact h hz

/-- System IR acceptance on quotes ⇒ Mathlib `A.mulVec x = b` (any `m×n`, `n ≠ 0`). -/
theorem system_of_isSystemSolution {m n : Nat} [NeZero n]
    (A : _root_.Matrix (Fin m) (Fin n) ℚ) (x : Fin n → ℚ) (b : Fin m → ℚ)
    (h : isSystemSolution (quoteMatrix A) (quoteVector b) (quoteVector x) = true) :
    A.mulVec x = b := by
  obtain ⟨ax, bv, hax, hbv, heq⟩ :=
    isSystemSolution_sound (quoteMatrix A) (quoteVector b) (quoteVector x) h
  have hAq := quoteMatrix_eval? A
  have hxq := quoteVector_eval? x
  have hbq := quoteVector_eval? b
  have hmul :
      mulRatsVec (List.ofFn fun i : Fin m => List.ofFn fun j : Fin n => A i j)
          (List.ofFn x) = some ax := by
    simpa [Matrix.mulVecEval?, hAq, hxq] using hax
  have hax' : ax = List.ofFn (A.mulVec x) :=
    Option.some.inj (hmul.symm.trans (mulRatsVec_ofFn A x))
  have hbv' : bv = List.ofFn b := by
    have : (quoteVector b).eval? = some bv := hbv
    rw [hbq] at this
    exact Option.some.inj this.symm
  have heq' : List.ofFn (A.mulVec x) = List.ofFn b := by
    have hx := (ratsEqual_eq (ax.map fun t => [t]) (bv.map fun t => [t])).1 heq
    have hsing := MathEvidence.Checkers.LinearAlgebra.singletonColumns_eq hx
    simpa [hax', hbv'] using hsing
  exact (List.ofFn_inj.mp heq')

theorem system_of_isSystemSolution_fin2
    (A : _root_.Matrix (Fin 2) (Fin 2) ℚ) (x b : Fin 2 → ℚ)
    (h : isSystemSolution (quoteMatrix A) (quoteVector b) (quoteVector x) = true) :
    A.mulVec x = b :=
  system_of_isSystemSolution A x b h

theorem system_of_isSystemSolution_fin3
    (A : _root_.Matrix (Fin 3) (Fin 3) ℚ) (x b : Fin 3 → ℚ)
    (h : isSystemSolution (quoteMatrix A) (quoteVector b) (quoteVector x) = true) :
    A.mulVec x = b :=
  system_of_isSystemSolution A x b h

/-- Kernel IR acceptance on quotes ⇒ Mathlib nonzero kernel vector (any `m×n`, `n ≠ 0`). -/
theorem kernel_of_isKernelVector {m n : Nat} [NeZero n]
    (A : _root_.Matrix (Fin m) (Fin n) ℚ) (v : Fin n → ℚ)
    (h : isKernelVector (quoteMatrix A) (quoteVector v) = true) :
    A.mulVec v = 0 ∧ v ≠ 0 := by
  obtain ⟨av, xv, hav, hxv, hz, hnz⟩ :=
    isKernelVector_sound (quoteMatrix A) (quoteVector v) h
  have hAq := quoteMatrix_eval? A
  have hvq := quoteVector_eval? v
  have hmul :
      mulRatsVec (List.ofFn fun i : Fin m => List.ofFn fun j : Fin n => A i j)
          (List.ofFn v) = some av := by
    simpa [Matrix.mulVecEval?, hAq, hvq] using hav
  have hav' : av = List.ofFn (A.mulVec v) :=
    Option.some.inj (hmul.symm.trans (mulRatsVec_ofFn A v))
  have hxv' : xv = List.ofFn v := by
    have : (quoteVector v).eval? = some xv := hxv
    rw [hvq] at this
    exact Option.some.inj this.symm
  have hzero : A.mulVec v = 0 := by
    have : isZeroRats (List.ofFn (A.mulVec v)) = true := by simpa [hav'] using hz
    exact (isZeroRats_ofFn (A.mulVec v)).1 this
  have hnz' : v ≠ 0 := by
    have : isNonzeroRats (List.ofFn v) = true := by simpa [hxv'] using hnz
    exact (isNonzeroRats_ofFn v).1 this
  exact ⟨hzero, hnz'⟩

theorem kernel_of_isKernelVector_fin2
    (A : _root_.Matrix (Fin 2) (Fin 2) ℚ) (v : Fin 2 → ℚ)
    (h : isKernelVector (quoteMatrix A) (quoteVector v) = true) :
    A.mulVec v = 0 ∧ v ≠ 0 :=
  kernel_of_isKernelVector A v h

theorem kernel_of_isKernelVector_fin3
    (A : _root_.Matrix (Fin 3) (Fin 3) ℚ) (v : Fin 3 → ℚ)
    (h : isKernelVector (quoteMatrix A) (quoteVector v) = true) :
    A.mulVec v = 0 ∧ v ≠ 0 :=
  kernel_of_isKernelVector A v h

end MathEvidence.Checkers.LinearAlgebra.Bridge
