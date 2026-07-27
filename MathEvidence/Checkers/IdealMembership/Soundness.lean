/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.RingTheory.Ideal.Basic
import Mathlib.RingTheory.Ideal.Span
import MathEvidence.IR.Polynomial.Soundness
import MathEvidence.Checkers.IdealMembership.Check

/-!
# Ideal-membership checker soundness (ME-RV-032)

`checkBool_sound` is the authority theorem: Boolean acceptance implies
Mathlib ideal membership of the interpreted target.
-/

namespace MathEvidence.Checkers.IdealMembership

open MathEvidence.IR.Polynomial
open MvPolynomial

/-- Mathlib membership claim established by a successful checker run. -/
def Claim.proposition {m : Nat} (c : Claim m) : Prop :=
  c.target.eval ∈
    Ideal.span (Set.range fun i : Fin c.generators.size => (c.generators[i]).eval)

private theorem checkBool_parts {m : Nat} (req : Request m) (cert : Certificate m)
    (h : checkBool req cert = true) :
    digestOk req cert = true ∧
      wellFormedOk req cert = true ∧
      resourceOk req cert = true ∧
      identityOk req cert = true := by
  -- checkBool = ((d && w) && r) && i
  simp only [checkBool, Bool.and_eq_true] at h
  exact ⟨h.1.1.1, h.1.1.2, h.1.2, h.2⟩

private theorem identityOk_eq {m : Nat} (req : Request m) (cert : Certificate m)
    (hid : identityOk req cert = true) :
    linearCombination req.claim.generators cert.multipliers =
      req.claim.target.normalize := by
  simpa [identityOk, beq_iff_eq] using hid

private theorem wellFormedOk_sizes {m : Nat} (req : Request m) (cert : Certificate m)
    (hwf : wellFormedOk req cert = true) :
    req.claim.generators.size = cert.multipliers.size ∧
      req.claim.generators.size ≥ 1 := by
  simpa [wellFormedOk, Bool.and_eq_true, beq_iff_eq, decide_eq_true_eq] using hwf

theorem checkBool_identity {m : Nat} (req : Request m) (cert : Certificate m)
    (h : checkBool req cert = true) :
    req.claim.target.eval =
      (linearCombination req.claim.generators cert.multipliers).eval := by
  have heq := identityOk_eq req cert (checkBool_parts req cert h).2.2.2
  calc
    req.claim.target.eval = req.claim.target.normalize.eval :=
      (SparsePoly.eval_normalize _).symm
    _ = (linearCombination req.claim.generators cert.multipliers).eval :=
      congrArg SparsePoly.eval heq.symm

theorem checkBool_sound {m : Nat} (req : Request m) (cert : Certificate m)
    (h : checkBool req cert = true) :
    req.claim.target.eval ∈
      Ideal.span
        (Set.range fun i : Fin req.claim.generators.size =>
          (req.claim.generators[i]).eval) := by
  have hlen := (wellFormedOk_sizes req cert (checkBool_parts req cert h).2.1).1
  have heq' := identityOk_eq req cert (checkBool_parts req cert h).2.2.2
  have heq :
      req.claim.target.normalize =
        linearCombinationList req.claim.generators.toList cert.multipliers.toList := by
    simpa [linearCombination] using heq'.symm
  have hlenL :
      req.claim.generators.toList.length = cert.multipliers.toList.length := by
    simpa using hlen
  have hmem := mem_span_of_linearCombination req.claim.target
    req.claim.generators.toList cert.multipliers.toList hlenL heq
  -- `Array.size` / `List.length` and `get` / `getElem` agree definitionally on `toList`.
  simpa [Array.length_toList, Array.getElem_toList] using hmem

/-- Legacy package acceptance implies span membership. -/
theorem checkMembership_sound {m : Nat}
    (f : SparsePoly m) (gens mults : Array (SparsePoly m))
    (h : checkMembership f gens mults = true) :
    f.eval ∈
      Ideal.span (Set.range fun i : Fin gens.size => (gens[i]).eval) := by
  have hparts : gens.size = mults.size ∧
      linearCombination gens mults = f.normalize := by
    simpa [checkMembership, Bool.and_eq_true, beq_iff_eq] using h
  have heq : f.normalize = linearCombinationList gens.toList mults.toList := by
    simpa [linearCombination] using hparts.2.symm
  have hmem := mem_span_of_linearCombination f gens.toList mults.toList
    (by simpa using hparts.1) heq
  simpa [Array.length_toList, Array.getElem_toList] using hmem

/-- Transport checker membership through reifier equalities (ME-RV-033/034). -/
theorem checkMembership_sound_transport {m : Nat}
    (f : SparsePoly m) (gens mults : Array (SparsePoly m))
    (target : MvPolynomial (Fin m) ℤ)
    (genEvals : Fin gens.size → MvPolynomial (Fin m) ℤ)
    (hf : f.eval = target)
    (hg : ∀ i : Fin gens.size, (gens[i]).eval = genEvals i)
    (h : checkMembership f gens mults = true) :
    target ∈ Ideal.span (Set.range genEvals) := by
  have hmem := checkMembership_sound f gens mults h
  rw [← hf]
  have hranges :
      (Set.range fun i : Fin gens.size => (gens[i]).eval) = Set.range genEvals := by
    ext x
    simp only [Set.mem_range]
    constructor
    · rintro ⟨i, rfl⟩
      exact ⟨i, (hg i).symm⟩
    · rintro ⟨i, rfl⟩
      exact ⟨i, hg i⟩
  rwa [hranges] at hmem

/-- Singleton span equals `Set.range` of a length-1 family. -/
theorem span_range_fin1 {R : Type*} [CommRing R] (g : R) :
    Ideal.span (Set.range fun _ : Fin 1 => g) = Ideal.span {g} := by
  have : Set.range (fun _ : Fin 1 => g) = ({g} : Set R) := by
    ext x
    constructor
    · rintro ⟨_, rfl⟩
      exact Set.mem_singleton _
    · intro hx
      exact ⟨0, (Set.mem_singleton_iff.mp hx).symm⟩
  rw [this]

/-- Two-element insert span equals `Set.range` of a length-2 family. -/
theorem span_range_fin2 {R : Type*} [CommRing R] (g₁ g₂ : R) :
    Ideal.span (Set.range ![g₁, g₂]) = Ideal.span {g₁, g₂} := by
  have : Set.range ![g₁, g₂] = ({g₁, g₂} : Set R) := by
    ext x
    constructor
    · rintro ⟨i, rfl⟩
      fin_cases i <;> simp
    · intro hx
      simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at hx
      rcases hx with rfl | rfl
      · exact ⟨0, by simp⟩
      · exact ⟨1, by simp⟩
  rw [this]

/-- Tactic close helper: singleton Mathlib span from IR check + reifier eqs. -/
theorem mem_span_singleton_of_check {m : Nat}
    (f g q : SparsePoly m)
    (target gMath : MvPolynomial (Fin m) ℤ)
    (hf : f.eval = target) (hg : g.eval = gMath)
    (h : checkMembership f #[g] #[q] = true) :
    target ∈ Ideal.span {gMath} := by
  have hmem :=
    checkMembership_sound_transport f #[g] #[q] target (fun _ : Fin 1 => gMath) hf
      (fun i => by fin_cases i; exact hg) h
  rwa [span_range_fin1 gMath] at hmem

/-- Tactic close helper: two-generator Mathlib span from IR check + reifier eqs. -/
theorem mem_span_pair_of_check {m : Nat}
    (f g₁ g₂ q₁ q₂ : SparsePoly m)
    (target gMath₁ gMath₂ : MvPolynomial (Fin m) ℤ)
    (hf : f.eval = target)
    (hg₁ : g₁.eval = gMath₁) (hg₂ : g₂.eval = gMath₂)
    (h : checkMembership f #[g₁, g₂] #[q₁, q₂] = true) :
    target ∈ Ideal.span {gMath₁, gMath₂} := by
  have hmem :=
    checkMembership_sound_transport f #[g₁, g₂] #[q₁, q₂] target ![gMath₁, gMath₂] hf
      (fun i => by
        match i with
        | ⟨0, _⟩ => simpa using hg₁
        | ⟨1, _⟩ => simpa using hg₂
        | ⟨n + 2, hlt⟩ =>
          exact (Nat.not_lt_zero _ (Nat.lt_of_succ_lt_succ (Nat.lt_of_succ_lt_succ hlt))).elim)
      h
  rwa [span_range_fin2 gMath₁ gMath₂] at hmem

/-- Three-element insert span equals `Set.range` of a length-3 family. -/
theorem span_range_fin3 {R : Type*} [CommRing R] (g₁ g₂ g₃ : R) :
    Ideal.span (Set.range ![g₁, g₂, g₃]) = Ideal.span {g₁, g₂, g₃} := by
  have : Set.range ![g₁, g₂, g₃] = ({g₁, g₂, g₃} : Set R) := by
    ext x
    constructor
    · rintro ⟨i, rfl⟩
      fin_cases i <;> simp [Set.mem_insert_iff]
    · intro hx
      simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at hx
      rcases hx with rfl | rfl | rfl
      · exact ⟨0, by simp⟩
      · exact ⟨1, by simp⟩
      · exact ⟨2, by simp⟩
  rw [this]

/-- Tactic close helper: three-generator Mathlib span (ME-RV-034 Fin-3). -/
theorem mem_span_triple_of_check {m : Nat}
    (f g₁ g₂ g₃ q₁ q₂ q₃ : SparsePoly m)
    (target gMath₁ gMath₂ gMath₃ : MvPolynomial (Fin m) ℤ)
    (hf : f.eval = target)
    (hg₁ : g₁.eval = gMath₁) (hg₂ : g₂.eval = gMath₂) (hg₃ : g₃.eval = gMath₃)
    (h : checkMembership f #[g₁, g₂, g₃] #[q₁, q₂, q₃] = true) :
    target ∈ Ideal.span {gMath₁, gMath₂, gMath₃} := by
  have hmem :=
    checkMembership_sound_transport f #[g₁, g₂, g₃] #[q₁, q₂, q₃] target
      ![gMath₁, gMath₂, gMath₃] hf
      (fun i => by
        match i with
        | ⟨0, _⟩ => simpa using hg₁
        | ⟨1, _⟩ => simpa using hg₂
        | ⟨2, _⟩ => simpa using hg₃
        | ⟨n + 3, hlt⟩ =>
          exact (Nat.not_lt_zero _
            (Nat.lt_of_succ_lt_succ
              (Nat.lt_of_succ_lt_succ (Nat.lt_of_succ_lt_succ hlt)))).elim)
      h
  rwa [span_range_fin3 gMath₁ gMath₂ gMath₃] at hmem

end MathEvidence.Checkers.IdealMembership
