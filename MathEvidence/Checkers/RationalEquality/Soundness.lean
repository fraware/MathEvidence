/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.SpecProp
import MathEvidence.IR.RationalExpr.Soundness

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.IR.RationalExpr

theorem checkBool_polyOk (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) : polyOk req = true := by
  simp [checkBool, Bool.and_eq_true] at h
  -- ((digestOk ∧ wellFormedOk) ∧ polyOk) ∧ coverOk
  exact h.1.2

theorem checkBool_coverOk (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) : coverOk req cert = true := by
  simp [checkBool, Bool.and_eq_true] at h
  -- ((digestOk ∧ wellFormedOk) ∧ polyOk) ∧ coverOk
  exact h.2

private theorem contains_true_iff_mem [DecidableEq α] (xs : List α) (x : α) :
    xs.contains x = true ↔ x ∈ xs := by
  induction xs with
  | nil =>
    simp
  | cons y ys ih =>
    by_cases hxy : x = y
    · subst hxy
      simp
    · simp [List.contains, hxy, ih]

private theorem factor_defined_nonzero
    (env : Env ℚ) (factors known : List Expr)
    (hconds : ∀ e ∈ factors ++ known, Defined env e ∧
      ∃ v, eval env e = some v ∧ v ≠ 0)
    {e : Expr} (he : e ∈ factors) :
    Defined env e ∧ ∃ v, eval env e = some v ∧ v ≠ 0 :=
  hconds e (List.mem_append_left known he)

private theorem defined_of_denominators_nonzero
    (env : Env ℚ) :
    (e : Expr) →
      (∀ d ∈ e.denominators, Defined env d ∧
        ∃ v, eval env d = some v ∧ v ≠ 0) →
      Defined env e := by
  intro e hdenoms
  induction e with
  | var _ => trivial
  | int _ => trivial
  | rat _ d =>
    have hz := hdenoms (.int (Int.ofNat d)) (by simp [Expr.denominators])
    obtain ⟨v, hev, hv⟩ := hz.2
    have hcast : (d : ℚ) ≠ 0 := by
      intro hd
      apply hv
      simpa [eval, hd] using hev.symm
    have hd : d ≠ 0 := by
      intro hd0
      exact hcast (by simp [hd0])
    exact ⟨hd, hcast⟩
  | neg e ih =>
    exact ih (by
      intro d hd
      exact hdenoms d (by simpa [Expr.denominators] using hd))
  | add a b iha ihb =>
    constructor
    · exact iha (by
        intro d hd
        exact hdenoms d (by simp [Expr.denominators, hd]))
    · exact ihb (by
        intro d hd
        exact hdenoms d (by simp [Expr.denominators, hd]))
  | sub a b iha ihb =>
    constructor
    · exact iha (by
        intro d hd
        exact hdenoms d (by simp [Expr.denominators, hd]))
    · exact ihb (by
        intro d hd
        exact hdenoms d (by simp [Expr.denominators, hd]))
  | mul a b iha ihb =>
    constructor
    · exact iha (by
        intro d hd
        exact hdenoms d (by simp [Expr.denominators, hd]))
    · exact ihb (by
        intro d hd
        exact hdenoms d (by simp [Expr.denominators, hd]))
  | pow b _ ih =>
    exact ih (by
      intro d hd
      exact hdenoms d (by simpa [Expr.denominators] using hd))
  | div n d ihn ihd =>
    have hn : Defined env n := ihn (by
      intro x hx
      exact hdenoms x (by simp [Expr.denominators, hx]))
    have hd : Defined env d := ihd (by
      intro x hx
      exact hdenoms x (by simp [Expr.denominators, hx]))
    have hd_nonzero := hdenoms d (by simp [Expr.denominators])
    obtain ⟨v, hev, hv⟩ := hd_nonzero.2
    refine ⟨hn, hd, ?_⟩
    intro hzero
    have hv0 : v = 0 := by
      simpa [hzero] using hev.symm
    exact hv hv0

theorem defined_of_denomsCovered
    (env : Env ℚ) (e : Expr) (factors known : List Expr)
    (hcover : denomsCovered e factors = true)
    (hconds : ∀ f ∈ factors ++ known, Defined env f ∧
      ∃ v, eval env f = some v ∧ v ≠ 0) :
    Defined env e := by
  apply defined_of_denominators_nonzero env e
  intro d hd
  have hcontains : factors.contains d = true := by
    exact List.all_eq_true.mp hcover d hd
  exact factor_defined_nonzero env factors known hconds
    ((contains_true_iff_mem factors d).1 hcontains)

theorem coverOk_defined_lhs (req : Request) (cert : Certificate) (env : Env ℚ)
    (hcover : coverOk req cert = true)
    (hconds : ∀ f ∈ cert.denomFactors ++ req.claim.knownAssumptions,
      Defined env f ∧ ∃ v, eval env f = some v ∧ v ≠ 0) :
    Defined env req.claim.lhs := by
  simp [coverOk, Bool.and_eq_true] at hcover
  exact defined_of_denomsCovered env req.claim.lhs cert.denomFactors
    req.claim.knownAssumptions hcover.1 hconds

theorem coverOk_defined_rhs (req : Request) (cert : Certificate) (env : Env ℚ)
    (hcover : coverOk req cert = true)
    (hconds : ∀ f ∈ cert.denomFactors ++ req.claim.knownAssumptions,
      Defined env f ∧ ∃ v, eval env f = some v ∧ v ≠ 0) :
    Defined env req.claim.rhs := by
  simp [coverOk, Bool.and_eq_true] at hcover
  exact defined_of_denomsCovered env req.claim.rhs cert.denomFactors
    req.claim.knownAssumptions hcover.2 hconds

theorem checkBool_sound (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) :
    Claim.proposition req.claim cert.denomFactors := by
  intro env hconds
  have hp : polyEqual req.claim.lhs req.claim.rhs = true := checkBool_polyOk req cert h
  have hcover : coverOk req cert = true := checkBool_coverOk req cert h
  have hl : Defined env req.claim.lhs := coverOk_defined_lhs req cert env hcover hconds
  have hr : Defined env req.claim.rhs := coverOk_defined_rhs req cert env hcover hconds
  exact eval_eq_of_polyEqual_defined req.claim.lhs req.claim.rhs env hp hl hr

theorem check_sound (req : Request) (cand : Candidate) (cert : Certificate)
    (h : check req cand cert = .accept) :
    Claim.proposition req.claim cert.denomFactors := by
  exact checkBool_sound req cert ((check_accept_iff req cand cert).1 h)

end MathEvidence.Checkers.RationalEquality
