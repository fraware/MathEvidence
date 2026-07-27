/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Algebra.BigOperators.Group.Finset
import Mathlib.Data.List.OfFn
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.LinearAlgebra.Matrix.Determinant.Basic
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring
import MathEvidence.Checkers.LinearAlgebra.Soundness
import MathEvidence.Encoding.Matrix
import MathEvidence.IR.MatrixExpr.Ops
import MathEvidence.IR.MatrixExpr.Soundness

/-!
# Determinant Mathlib transport (ME-RV-040)

Non-partial fuel `detRats` matches Mathlib `Matrix.det` for every square `Fin n`,
via closed forms (`n ≤ 4`) and Laplace + `det_succ_row_zero` (`n > 4`).
-/

namespace MathEvidence.Checkers.LinearAlgebra.Bridge

open Matrix
open MathEvidence.IR.MatrixExpr
open MathEvidence.Encoding.Matrix

/-- Dense `List.ofFn` encoding of a square Mathlib matrix. -/
def ofFnSquare {n : Nat} (A : _root_.Matrix (Fin n) (Fin n) ℚ) : List (List ℚ) :=
  List.ofFn fun i : Fin n => List.ofFn fun j : Fin n => A i j

private theorem ofFnSquare_length {n : Nat} (A : _root_.Matrix (Fin n) (Fin n) ℚ) :
    (ofFnSquare A).length = n := by
  simp [ofFnSquare, List.length_ofFn]

private theorem ofFnSquare_all_square {n : Nat} (A : _root_.Matrix (Fin n) (Fin n) ℚ) :
    (ofFnSquare A).all (fun r => decide (r.length = n)) = true := by
  refine (List.all_eq_true).2 ?_
  intro row hr
  rw [ofFnSquare, List.mem_ofFn, Set.mem_range] at hr
  obtain ⟨_, rfl⟩ := hr
  simp [List.length_ofFn]

private theorem ofFnSquare_isEmpty_succ {n : Nat} (A : _root_.Matrix (Fin (n + 1)) (Fin (n + 1)) ℚ) :
    (ofFnSquare A).isEmpty = false := by
  simp [ofFnSquare, List.ofFn_succ]

private theorem laplaceSign_eq (j : Nat) : laplaceSign j = (-1 : ℚ) ^ j := by
  induction j with
  | zero => rfl
  | succ j ih =>
    have hneg : laplaceSign (j + 1) = -(laplaceSign j) := by
      simp only [laplaceSign]
      rcases Nat.mod_two_eq_zero_or_one j with hj | hj
      · have : (j + 1) % 2 = 1 := by omega
        simp [hj, this]
      · have : (j + 1) % 2 = 0 := by omega
        simp [hj, this]
    rw [hneg, ih, pow_succ]
    ring

/-- `eraseIdx 0` on `ofFn` recovers the successor embedding. -/
private theorem eraseIdx_zero_ofFn {n : Nat} {α : Type*} (f : Fin (n + 1) → α) :
    (List.ofFn f).eraseIdx 0 = List.ofFn fun i : Fin n => f i.succ := by
  rw [List.ofFn_succ, List.eraseIdx_cons_zero]

/-- `eraseIdx j` on `ofFn` matches `Fin.succAbove`. -/
private theorem eraseIdx_ofFn_succAbove {n : Nat} {α : Type*}
    (f : Fin (n + 1) → α) (j : Fin (n + 1)) :
    (List.ofFn f).eraseIdx j.val = List.ofFn fun i : Fin n => f (j.succAbove i) := by
  induction n with
  | zero =>
    have hj : j = 0 := Fin.eq_of_val_eq (Nat.lt_one_iff.mp j.isLt)
    subst hj
    simp [List.ofFn_succ, List.ofFn_zero, Fin.zero_succAbove]
  | succ n ih =>
    rw [List.ofFn_succ]
    cases j using Fin.cases with
    | zero =>
      simp [List.eraseIdx_cons_zero, Fin.zero_succAbove]
    | succ j =>
      simp only [Fin.val_succ, List.eraseIdx_cons_succ]
      have htail :
          (List.ofFn fun i : Fin (n + 1) => f i.succ).eraseIdx j.val =
            List.ofFn fun i : Fin n => f (j.succAbove i).succ :=
        ih (fun i => f i.succ) j
      rw [htail, List.ofFn_succ, Fin.succ_succAbove_zero]
      refine congrArg (_ :: ·) ?_
      refine congrArg List.ofFn ?_
      funext i
      rw [Fin.succ_succAbove_succ]

/-- Row-0 / column-`j` IR minor equals Mathlib `submatrix Fin.succ j.succAbove`. -/
theorem minorRats_ofFnSquare_row0 {n : Nat}
    (A : _root_.Matrix (Fin (n + 1)) (Fin (n + 1)) ℚ) (j : Fin (n + 1)) :
    minorRats (ofFnSquare A) 0 j.val =
      ofFnSquare (A.submatrix Fin.succ j.succAbove) := by
  simp only [minorRats, ofFnSquare, eraseIdx_zero_ofFn]
  refine List.ext_getElem (by simp [List.length_map, List.length_ofFn]) ?_
  intro i hi _
  have hiFin : i < n := by simpa [List.length_map, List.length_ofFn] using hi
  simp only [List.getElem_map, List.getElem_ofFn]
  rw [eraseIdx_ofFn_succAbove (fun col => A (Fin.succ ⟨i, hiFin⟩) col) j]
  simp [Matrix.submatrix_apply, List.getElem_ofFn]

private theorem mapM_range_eq_ofFn {n : Nat} {α : Type*}
    (f : Nat → Option α) (g : Fin n → α)
    (hf : ∀ i : Fin n, f i.val = some (g i)) :
    (List.range n).mapM f = some (List.ofFn g) := by
  induction n with
  | zero =>
    rfl
  | succ n ih =>
    have hprefix :
        (List.range n).mapM f =
          some (List.ofFn fun i : Fin n => g i.castSucc) :=
      ih (fun i : Fin n => g i.castSucc) (fun i => hf i.castSucc)
    have hlast : f n = some (g (Fin.last n)) := hf (Fin.last n)
    rw [List.range_succ, List.mapM_append]
    simp only [hprefix, List.mapM_cons, hlast, List.mapM_nil, Option.bind_eq_bind,
      Option.some_bind]
    exact congrArg some <| by
      simpa [← List.concat_eq_append] using (List.ofFn_succ' g).symm

private theorem foldl_add_const (c : ℚ) (xs : List ℚ) :
    xs.foldl (fun acc x => acc + x) c = c + xs.foldl (fun acc x => acc + x) 0 := by
  induction xs generalizing c with
  | nil => simp
  | cons x xs ih =>
    simp only [List.foldl_cons]
    rw [ih (c + x), zero_add, ih x, add_assoc]

private theorem sumRats_ofFn {n : Nat} (f : Fin n → ℚ) :
    sumRats (List.ofFn f) = ∑ i : Fin n, f i := by
  induction n with
  | zero =>
    simp [sumRats, List.ofFn_zero]
  | succ n ih =>
    rw [List.ofFn_succ, Fin.sum_univ_succ, sumRats, List.foldl_cons, zero_add,
      foldl_add_const]
    have hrest :
        sumRats (List.ofFn fun i : Fin n => f i.succ) = ∑ i : Fin n, f i.succ :=
      ih fun i => f i.succ
    simpa [sumRats] using congrArg (fun t => f 0 + t) hrest

private theorem succ_two_eq_three : Fin.succ (2 : Fin 3) = (3 : Fin 4) := rfl
private theorem succAbove_fin4_one_zero : (1 : Fin 4).succAbove (0 : Fin 3) = 0 := rfl
private theorem succAbove_fin4_one_one : (1 : Fin 4).succAbove (1 : Fin 3) = 2 := rfl
private theorem succAbove_fin4_one_two : (1 : Fin 4).succAbove (2 : Fin 3) = 3 := rfl
private theorem succAbove_fin4_two_zero : (2 : Fin 4).succAbove (0 : Fin 3) = 0 := rfl
private theorem succAbove_fin4_two_one : (2 : Fin 4).succAbove (1 : Fin 3) = 1 := rfl
private theorem succAbove_fin4_two_two : (2 : Fin 4).succAbove (2 : Fin 3) = 3 := rfl
private theorem succAbove_fin4_three_zero : (3 : Fin 4).succAbove (0 : Fin 3) = 0 := rfl
private theorem succAbove_fin4_three_one : (3 : Fin 4).succAbove (1 : Fin 3) = 1 := rfl
private theorem succAbove_fin4_three_two : (3 : Fin 4).succAbove (2 : Fin 3) = 2 := rfl
private theorem castAdd_one_zero_fin4 : Fin.castAdd 1 (0 : Fin 3) = (0 : Fin 4) := rfl
private theorem castAdd_one_one_fin4 : Fin.castAdd 1 (1 : Fin 3) = (1 : Fin 4) := rfl

/-- IR `detRatsSmall` matches Mathlib `det` on Fin 4. -/
theorem detRatsSmall_ofFnSquare_fin4
    (A : _root_.Matrix (Fin 4) (Fin 4) ℚ) :
    detRatsSmall (ofFnSquare A) = some A.det := by
  have hdet :
      A.det =
        A 0 0 * (A.submatrix Fin.succ (0 : Fin 4).succAbove).det -
          A 0 1 * (A.submatrix Fin.succ (1 : Fin 4).succAbove).det +
          A 0 2 * (A.submatrix Fin.succ (2 : Fin 4).succAbove).det -
          A 0 3 * (A.submatrix Fin.succ (3 : Fin 4).succAbove).det := by
    have hpow0 : (-1 : ℚ) ^ (0 : ℕ) = 1 := pow_zero _
    have hpow1 : (-1 : ℚ) ^ (1 : ℕ) = -1 := by norm_num
    have hpow2 : (-1 : ℚ) ^ (2 : ℕ) = 1 := by norm_num
    have hpow3 : (-1 : ℚ) ^ (3 : ℕ) = -1 := by norm_num
    have v3 : ((3 : Fin 4) : ℕ) = 3 := rfl
    rw [Matrix.det_succ_row_zero]
    simp [Fin.sum_univ_four, Fin.val_zero, Fin.val_one, Fin.val_two, v3, hpow0, hpow1,
      hpow2, hpow3, one_mul, mul_assoc, mul_one, sub_eq_add_neg]
  have h0 :
      (A.submatrix Fin.succ (0 : Fin 4).succAbove).det =
        A 1 1 * A 2 2 * A 3 3 - A 1 1 * A 2 3 * A 3 2
          - A 1 2 * A 2 1 * A 3 3 + A 1 2 * A 2 3 * A 3 1
          + A 1 3 * A 2 1 * A 3 2 - A 1 3 * A 2 2 * A 3 1 := by
    simp [Matrix.det_fin_three, Matrix.submatrix_apply, Fin.zero_succAbove,
      Fin.succ_zero_eq_one, Fin.succ_one_eq_two, succ_two_eq_three]
  have h1 :
      (A.submatrix Fin.succ (1 : Fin 4).succAbove).det =
        A 1 0 * A 2 2 * A 3 3 - A 1 0 * A 2 3 * A 3 2
          - A 1 2 * A 2 0 * A 3 3 + A 1 2 * A 2 3 * A 3 0
          + A 1 3 * A 2 0 * A 3 2 - A 1 3 * A 2 2 * A 3 0 := by
    simp [Matrix.det_fin_three, Matrix.submatrix_apply, Fin.succ_succAbove_zero,
      Fin.succ_succAbove_one, succAbove_fin4_one_zero, succAbove_fin4_one_one,
      succAbove_fin4_one_two, Fin.succ_zero_eq_one, Fin.succ_one_eq_two,
      succ_two_eq_three]
  have h2 :
      (A.submatrix Fin.succ (2 : Fin 4).succAbove).det =
        A 1 0 * A 2 1 * A 3 3 - A 1 0 * A 2 3 * A 3 1
          - A 1 1 * A 2 0 * A 3 3 + A 1 1 * A 2 3 * A 3 0
          + A 1 3 * A 2 0 * A 3 1 - A 1 3 * A 2 1 * A 3 0 := by
    simp [Matrix.det_fin_three, Matrix.submatrix_apply, succAbove_fin4_two_zero,
      succAbove_fin4_two_one, succAbove_fin4_two_two, Fin.succ_zero_eq_one,
      Fin.succ_one_eq_two, succ_two_eq_three, castAdd_one_zero_fin4,
      castAdd_one_one_fin4]
  have h3 :
      (A.submatrix Fin.succ (3 : Fin 4).succAbove).det =
        A 1 0 * A 2 1 * A 3 2 - A 1 0 * A 2 2 * A 3 1
          - A 1 1 * A 2 0 * A 3 2 + A 1 1 * A 2 2 * A 3 0
          + A 1 2 * A 2 0 * A 3 1 - A 1 2 * A 2 1 * A 3 0 := by
    simp [Matrix.det_fin_three, Matrix.submatrix_apply, succAbove_fin4_three_zero,
      succAbove_fin4_three_one, succAbove_fin4_three_two, Fin.succ_zero_eq_one,
      Fin.succ_one_eq_two, succ_two_eq_three]
  have hIR :
      detRatsSmall (ofFnSquare A) =
        some (
          A 0 0 *
              (A 1 1 * A 2 2 * A 3 3 - A 1 1 * A 2 3 * A 3 2
                - A 1 2 * A 2 1 * A 3 3 + A 1 2 * A 2 3 * A 3 1
                + A 1 3 * A 2 1 * A 3 2 - A 1 3 * A 2 2 * A 3 1) -
            A 0 1 *
              (A 1 0 * A 2 2 * A 3 3 - A 1 0 * A 2 3 * A 3 2
                - A 1 2 * A 2 0 * A 3 3 + A 1 2 * A 2 3 * A 3 0
                + A 1 3 * A 2 0 * A 3 2 - A 1 3 * A 2 2 * A 3 0) +
            A 0 2 *
              (A 1 0 * A 2 1 * A 3 3 - A 1 0 * A 2 3 * A 3 1
                - A 1 1 * A 2 0 * A 3 3 + A 1 1 * A 2 3 * A 3 0
                + A 1 3 * A 2 0 * A 3 1 - A 1 3 * A 2 1 * A 3 0) -
            A 0 3 *
              (A 1 0 * A 2 1 * A 3 2 - A 1 0 * A 2 2 * A 3 1
                - A 1 1 * A 2 0 * A 3 2 + A 1 1 * A 2 2 * A 3 0
                + A 1 2 * A 2 0 * A 3 1 - A 1 2 * A 2 1 * A 3 0)) := by
    simp [ofFnSquare, detRatsSmall, detRatsUpTo3, fin4Minor0, fin4Minor1, fin4Minor2,
      fin4Minor3, List.ofFn_succ, List.ofFn_zero, List.getD_cons_zero, List.getD_cons_succ,
      List.length_ofFn, decide_True, Bool.and_self, Option.bind_eq_bind, Option.some_bind,
      pure, Fin.succ_zero_eq_one, Fin.succ_one_eq_two, succ_two_eq_three]
  rw [hIR, hdet, h0, h1, h2, h3]

private theorem detRatsSmall_ofFnSquare_le4 :
    ∀ (n : Nat) (_hn : n ≤ 4) (A : _root_.Matrix (Fin n) (Fin n) ℚ),
      detRatsSmall (ofFnSquare A) = some A.det
  | 0, _, A => by
    simp [ofFnSquare, detRatsSmall, detRatsUpTo3, List.ofFn_zero, Matrix.det_fin_zero]
  | 1, _, A => by
    simp [ofFnSquare, detRatsSmall, detRatsUpTo3, List.ofFn_succ, List.ofFn_zero,
      Matrix.det_fin_one, List.getD_cons_zero]
  | 2, _, A => by
    simp [ofFnSquare, detRatsSmall, detRatsUpTo3, List.ofFn_succ, List.ofFn_zero,
      Matrix.det_fin_two, List.getD_cons_zero, List.getD_cons_succ]
  | 3, _, A => by
    simp [ofFnSquare, detRatsSmall, detRatsUpTo3, List.ofFn_succ, List.ofFn_zero,
      Matrix.det_fin_three, List.getD_cons_zero, List.getD_cons_succ]
  | 4, _, A =>
    detRatsSmall_ofFnSquare_fin4 A
  | n + 5, hn, _ => by
    omega

/-- Fuel IR determinant matches Mathlib on every square `ofFn` matrix. -/
theorem detRatsFuel_ofFnSquare :
    ∀ (n : Nat) (A : _root_.Matrix (Fin n) (Fin n) ℚ),
      detRatsFuel n (ofFnSquare A) = some A.det := by
  intro n
  induction n with
  | zero =>
    intro A
    simp [detRatsFuel, ofFnSquare, List.ofFn_zero, Matrix.det_fin_zero]
  | succ n ih =>
    intro A
    have hall := ofFnSquare_all_square A
    have hempty := ofFnSquare_isEmpty_succ A
    by_cases hle : n + 1 ≤ 4
    · have hfuel :
          detRatsFuel (n + 1) (ofFnSquare A) = detRatsSmall (ofFnSquare A) := by
        unfold detRatsFuel
        simp [hempty, ofFnSquare_length, hall, hle]
      rw [hfuel, detRatsSmall_ofFnSquare_le4 (n + 1) hle A]
    · obtain ⟨rest, hcons⟩ :
          ∃ rest, ofFnSquare A =
            (List.ofFn fun col : Fin (n + 1) => A 0 col) :: rest := by
        refine ⟨List.ofFn fun i : Fin n => List.ofFn fun j : Fin (n + 1) => A i.succ j, ?_⟩
        simp [ofFnSquare, List.ofFn_succ]
      have hlen : (ofFnSquare A).length = n + 1 := ofFnSquare_length A
      have hrestLen : rest.length = n := by
        have h := congrArg List.length hcons
        simp only [hlen, List.length_cons, List.length_ofFn] at h
        omega
      have hfuel :
          detRatsFuel (n + 1) (ofFnSquare A) =
            match (List.range (n + 1)).mapM fun j => do
                let d ← detRatsFuel n (minorRats (ofFnSquare A) 0 j)
                pure (laplaceCofactorTerm d
                  (List.ofFn fun col : Fin (n + 1) => A 0 col) j)
            with
            | none => none
            | some terms => some (sumRats terms) := by
        simp only [detRatsFuel, hempty, hlen, hall, hle, ↓reduceIte]
        rw [hcons]
        simp only [List.length_cons, hrestLen]
        simp only [← hcons, ↓reduceIte]
        rfl
      have hmap :
          (List.range (n + 1)).mapM
              (fun j => do
                let d ← detRatsFuel n (minorRats (ofFnSquare A) 0 j)
                pure (laplaceCofactorTerm d
                  (List.ofFn fun col : Fin (n + 1) => A 0 col) j)) =
            some (List.ofFn fun j : Fin (n + 1) =>
              (-1 : ℚ) ^ (j : ℕ) * A 0 j *
                (A.submatrix Fin.succ j.succAbove).det) := by
        refine mapM_range_eq_ofFn _ _ ?_
        intro j
        have hminor := minorRats_ofFnSquare_row0 A j
        have hid := ih (A.submatrix Fin.succ j.succAbove)
        have hlt : j.val < (List.ofFn fun col : Fin (n + 1) => A 0 col).length := by
          simpa [List.length_ofFn] using j.isLt
        have hgetElem :
            (List.ofFn fun col : Fin (n + 1) => A 0 col)[j.val]'hlt = A 0 j :=
          List.getElem_ofFn (fun col : Fin (n + 1) => A 0 col) j.val hlt
        have hget :
            (List.ofFn fun col : Fin (n + 1) => A 0 col).getD j.val 0 = A 0 j := by
          rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem hlt, hgetElem]
          rfl
        rw [hminor, hid]
        simp only [Option.bind_eq_bind, Option.some_bind, laplaceCofactorTerm,
          laplaceSign_eq, hget, pure]
      have hsum :
          sumRats (List.ofFn fun j : Fin (n + 1) =>
              (-1 : ℚ) ^ (j : ℕ) * A 0 j *
                (A.submatrix Fin.succ j.succAbove).det) =
            A.det := by
        rw [sumRats_ofFn, Matrix.det_succ_row_zero]
      rw [hfuel, hmap]
      exact congrArg some hsum

/-- IR `detRats` matches Mathlib `det` on every square `ofFn` matrix. -/
theorem detRats_ofFnSquare {n : Nat} (A : _root_.Matrix (Fin n) (Fin n) ℚ) :
    detRats (ofFnSquare A) = some A.det := by
  simpa [detRats, ofFnSquare_length] using detRatsFuel_ofFnSquare n A

/-- Quoted matrices are well-formed (square case). -/
private theorem quoteMatrix_wellFormed_square {n : Nat}
    (A : _root_.Matrix (Fin n) (Fin n) ℚ) :
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

/-- Quoted-matrix eval recovers `ofFnSquare`. -/
private theorem quoteMatrix_eval?_square {n : Nat} (A : _root_.Matrix (Fin n) (Fin n) ℚ) :
    (quoteMatrix A).eval? = some (ofFnSquare A) := by
  simp only [Matrix.eval?, quoteMatrix_wellFormed_square, Bool.not_true, ofFnSquare]
  exact interprets_quoteMatrix A

/-- Det transport for every square size (ME-RV-040). -/
theorem det_of_isDetIdentity {n : Nat}
    (A : _root_.Matrix (Fin n) (Fin n) ℚ) (q : ℚ)
    (h : isDetIdentity (quoteMatrix A) (RatLit.ofRat q) = true) :
    A.det = q := by
  obtain ⟨detA, dq, hd, hq, heq⟩ :=
    isDetIdentity_sound (quoteMatrix A) (RatLit.ofRat q) h
  have hAq := quoteMatrix_eval?_square A
  have hto : (RatLit.ofRat q).toRat? = some q := by
    simp [RatLit.ofRat, RatLit.toRat?, Rat.den_nz, Rat.num_div_den]
  have hq' : dq = q := Option.some.inj (hq.symm.trans hto)
  have hmatch := detRats_ofFnSquare A
  have hdet : detA = A.det := by
    have hd' : detRats (ofFnSquare A) = some detA := by
      simp only [Matrix.detEval?] at hd
      rw [hAq] at hd
      simp only [Option.bind_eq_bind, Option.some_bind, quoteMatrix, ne_eq,
        not_true_eq_false, ↓reduceIte] at hd
      exact hd
    exact Option.some.inj (hd'.symm.trans hmatch)
  exact hdet.symm.trans (heq.trans hq')

theorem det_of_isDetIdentity_fin2
    (A : _root_.Matrix (Fin 2) (Fin 2) ℚ) (q : ℚ)
    (h : isDetIdentity (quoteMatrix A) (RatLit.ofRat q) = true) :
    A.det = q :=
  det_of_isDetIdentity A q h

theorem det_of_isDetIdentity_fin3
    (A : _root_.Matrix (Fin 3) (Fin 3) ℚ) (q : ℚ)
    (h : isDetIdentity (quoteMatrix A) (RatLit.ofRat q) = true) :
    A.det = q :=
  det_of_isDetIdentity A q h

theorem det_of_isDetIdentity_fin4
    (A : _root_.Matrix (Fin 4) (Fin 4) ℚ) (q : ℚ)
    (h : isDetIdentity (quoteMatrix A) (RatLit.ofRat q) = true) :
    A.det = q :=
  det_of_isDetIdentity A q h

theorem det_of_isDetIdentity_fin5
    (A : _root_.Matrix (Fin 5) (Fin 5) ℚ) (q : ℚ)
    (h : isDetIdentity (quoteMatrix A) (RatLit.ofRat q) = true) :
    A.det = q :=
  det_of_isDetIdentity A q h

theorem det_of_isDetIdentity_fin6
    (A : _root_.Matrix (Fin 6) (Fin 6) ℚ) (q : ℚ)
    (h : isDetIdentity (quoteMatrix A) (RatLit.ofRat q) = true) :
    A.det = q :=
  det_of_isDetIdentity A q h

end MathEvidence.Checkers.LinearAlgebra.Bridge
