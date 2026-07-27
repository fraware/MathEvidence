/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Analysis.Calculus.Deriv.Mul
import Mathlib.Analysis.Calculus.Deriv.Inv
import Mathlib.Analysis.Calculus.Deriv.Pow
import Mathlib.Analysis.Calculus.Deriv.Comp
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Deriv
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring
import MathEvidence.Checkers.AnalyticCalculus.Check
import MathEvidence.IR.AnalyticExpr.Interpret

/-!
# Analytic calculus soundness (ME-RV-052, ME-RV-053)

`checkDeriv_sound`: Boolean acceptance plus domain hypotheses yields
`HasDerivAt` (and `HasDerivWithinAt` on an explicit set).

`checkODE_sound`: residual tree + IC hypotheses yield
`CandidateSolvesFirstOrderODE`.
-/

namespace MathEvidence.Checkers.AnalyticCalculus

open MathEvidence.IR.AnalyticExpr

set_option maxHeartbeats 4000000

/-- Invert `some a = some b`. -/
private theorem some_inj {α : Type*} {a b : α} (h : some a = some b) : a = b :=
  Option.some.inj h

theorem obligationNonzeroOk_holds
    (obls : Array DomainObligation) (id : Nat) (e : Expr) (x : ℝ)
    (hok : obligationNonzeroOk obls id e = true)
    (hdom : SatisfiesObligations obls x) :
    e.interpret x ≠ 0 := by
  simp only [obligationNonzeroOk] at hok
  split_ifs at hok with hlt
  · cases hobl : obls[id] with
    | nonzero e' =>
      simp [hobl, decide_eq_true_eq] at hok
      subst hok
      have := hdom ⟨id, hlt⟩
      simpa [hobl, DomainObligation.holds] using this
    | positive _ | member _ _ =>
      simp [hobl] at hok

theorem obligationPositiveOk_holds
    (obls : Array DomainObligation) (id : Nat) (e : Expr) (x : ℝ)
    (hok : obligationPositiveOk obls id e = true)
    (hdom : SatisfiesObligations obls x) :
    0 < e.interpret x := by
  simp only [obligationPositiveOk] at hok
  split_ifs at hok with hlt
  · cases hobl : obls[id] with
    | positive e' =>
      simp [hobl, decide_eq_true_eq] at hok
      subst hok
      have := hdom ⟨id, hlt⟩
      simpa [hobl, DomainObligation.holds] using this
    | nonzero _ | member _ _ =>
      simp [hobl] at hok

/-- Inductive authority: well-typed derivation tree implies `HasDerivAt`. -/
theorem reconstructDeriv_sound
    (e : Expr) (p : DerivProof) (d : Expr)
    (obls : Array DomainObligation) (x : ℝ)
    (hcheck : checkProof e p obls = true)
    (hrec : reconstructDeriv e p = some d)
    (hdom : SatisfiesObligations obls x) :
    HasDerivAt e.interpret (d.interpret x) x := by
  induction p generalizing e d with
  | «variable» =>
    cases e with
    | «variable» i =>
      cases i with
      | zero =>
        simp only [reconstructDeriv, checkProof] at hrec hcheck
        injection hrec with hdeq
        subst hdeq
        simpa [interpret_variable0, interpret_const] using
          (hasDerivAt_id (𝕜 := ℝ) x)
      | succ _ =>
        simp [checkProof] at hcheck
    | _ =>
      simp [checkProof] at hcheck
  | «const» =>
    cases e with
    | «const» q =>
      simp only [reconstructDeriv, checkProof] at hrec hcheck
      injection hrec with hdeq
      subst hdeq
      have h := hasDerivAt_const (𝕜 := ℝ) x (q : ℝ)
      simpa [interpret_const] using h
    | _ =>
      simp [checkProof] at hcheck
  | neg p ih =>
    cases e with
    | neg a =>
      simp only [reconstructDeriv, checkProof] at hrec hcheck
      cases hda : reconstructDeriv a p with
      | none => simp [hda] at hrec
      | some da =>
        simp [hda, Option.map_some] at hrec
        subst hrec
        have hda_sound := ih a da hcheck hda
        rw [interpret_neg a, interpret_neg da]
        exact hda_sound.neg
    | _ =>
      simp [checkProof] at hcheck
  | add p q ihp ihq =>
    cases e with
    | add a b =>
      simp only [reconstructDeriv, checkProof, Bool.and_eq_true] at hrec hcheck
      rcases hcheck with ⟨ha, hb⟩
      cases hda : reconstructDeriv a p with
      | none => simp [hda] at hrec
      | some da =>
        cases hdb : reconstructDeriv b q with
        | none => simp [hda, hdb] at hrec
        | some db =>
          simp [hda, hdb] at hrec
          subst hrec
          have ha' := ihp a da ha hda
          have hb' := ihq b db hb hdb
          rw [interpret_add a b, interpret_add da db]
          exact ha'.add hb'
    | _ =>
      simp [checkProof] at hcheck
  | sub p q ihp ihq =>
    cases e with
    | sub a b =>
      simp only [reconstructDeriv, checkProof, Bool.and_eq_true] at hrec hcheck
      rcases hcheck with ⟨ha, hb⟩
      cases hda : reconstructDeriv a p with
      | none => simp [hda] at hrec
      | some da =>
        cases hdb : reconstructDeriv b q with
        | none => simp [hda, hdb] at hrec
        | some db =>
          simp [hda, hdb] at hrec
          subst hrec
          have ha' := ihp a da ha hda
          have hb' := ihq b db hb hdb
          rw [interpret_sub a b, interpret_sub da db]
          exact ha'.sub hb'
    | _ =>
      simp [checkProof] at hcheck
  | mul p q ihp ihq =>
    cases e with
    | mul a b =>
      simp only [reconstructDeriv, checkProof, Bool.and_eq_true] at hrec hcheck
      rcases hcheck with ⟨ha, hb⟩
      cases hda : reconstructDeriv a p with
      | none => simp [hda] at hrec
      | some da =>
        cases hdb : reconstructDeriv b q with
        | none => simp [hda, hdb] at hrec
        | some db =>
          simp [hda, hdb] at hrec
          subst hrec
          have ha' := ihp a da ha hda
          have hb' := ihq b db hb hdb
          simpa [interpret_mul, interpret_add, mul_comm, mul_left_comm, mul_assoc, add_comm] using
            ha'.mul hb'
    | _ =>
      simp [checkProof] at hcheck
  | inv p id ih =>
    cases e with
    | inv a =>
      simp only [reconstructDeriv, checkProof, Bool.and_eq_true] at hrec hcheck
      rcases hcheck with ⟨hobl, ha⟩
      cases hda : reconstructDeriv a p with
      | none => simp [hda] at hrec
      | some da =>
        simp [hda] at hrec
        subst hrec
        have ha' := ih a da ha hda
        have hne := obligationNonzeroOk_holds obls id a x hobl hdom
        have hinv := ha'.inv hne
        -- IR derivative `- (da / (a*a))` matches Mathlib `-f' / f^2`.
        rw [interpret_inv]
        have hval :
            (Expr.neg (Expr.div da (Expr.mul a a))).interpret x =
              -da.interpret x / a.interpret x ^ 2 := by
          simp only [interpret_neg, interpret_div, interpret_mul, pow_two]
          ring
        rw [hval]
        exact hinv
    | _ =>
      simp [checkProof] at hcheck
  | div p q id ihp ihq =>
    cases e with
    | div n den =>
      simp only [reconstructDeriv, checkProof, Bool.and_eq_true] at hrec hcheck
      -- Left-assoc: `(obl && check n) && check den`.
      rcases hcheck with ⟨⟨hobl, hn⟩, hd⟩
      cases hdn : reconstructDeriv n p with
      | none => simp [hdn] at hrec
      | some dn =>
        cases hdd : reconstructDeriv den q with
        | none => simp [hdn, hdd] at hrec
        | some dd =>
          simp [hdn, hdd] at hrec
          subst hrec
          have hn' := ihp n dn hn hdn
          have hd' := ihq den dd hd hdd
          have hne := obligationNonzeroOk_holds obls id den x hobl hdom
          have hdiv := hn'.div hd' hne
          simpa [interpret_div, interpret_sub, interpret_mul, pow_two, div_eq_mul_inv,
            mul_comm, mul_left_comm, mul_assoc, sub_eq_add_neg] using hdiv
    | _ =>
      simp [checkProof] at hcheck
  | «pow» n p ih =>
    match e with
    | .pow a n' =>
      simp only [reconstructDeriv, checkProof, Bool.and_eq_true] at hrec hcheck
      rcases hcheck with ⟨hk, ha⟩
      obtain rfl : n' = n := by simpa [decide_eq_true_eq, eq_comm] using hk
      match hda : reconstructDeriv a p with
      | none => simp [hda] at hrec
      | some da =>
        simp [hda] at hrec
        split_ifs at hrec with hn0
        · have hdeq := some_inj hrec
          subst hdeq
          simpa [interpret_pow, interpret_const, pow_zero, hn0] using
            (hasDerivAt_const (𝕜 := ℝ) x (1 : ℝ))
        · have hdeq := some_inj hrec
          subst hdeq
          have ha' := ih a da ha hda
          -- After `obtain rfl`, the surviving exponent name is `n'`.
          have hpow := HasDerivAt.pow (n := n') ha'
          simpa [interpret_pow, interpret_mul, interpret_const, Nat.cast_eq_ofNat,
            mul_comm, mul_left_comm, mul_assoc] using hpow
    | .variable _ | .const _ | .add _ _ | .sub _ _ | .mul _ _ | .div _ _ | .inv _ | .neg _
    | .sin _ | .cos _ | .exp _ | .log _ =>
      simp [checkProof] at hcheck
  | sin p ih =>
    match e with
    | .sin a =>
      simp only [reconstructDeriv, checkProof] at hrec hcheck
      match hda : reconstructDeriv a p with
      | none => simp [hda] at hrec
      | some da =>
        simp [hda] at hrec
        subst hrec
        have ha' := ih a da hcheck hda
        have hsin := HasDerivAt.comp x (Real.hasDerivAt_sin (a.interpret x)) ha'
        simpa [interpret_sin, interpret_mul, interpret_cos, Function.comp, mul_comm] using hsin
    | .variable _ | .const _ | .add _ _ | .sub _ _ | .mul _ _ | .div _ _ | .inv _ | .neg _
    | .pow _ _ | .cos _ | .exp _ | .log _ =>
      simp [checkProof] at hcheck
  | «exp» p ih =>
    match e with
    | .exp a =>
      simp only [reconstructDeriv, checkProof] at hrec hcheck
      match hda : reconstructDeriv a p with
      | none => simp [hda] at hrec
      | some da =>
        simp [hda] at hrec
        subst hrec
        have ha' := ih a da hcheck hda
        have hexp := HasDerivAt.comp x (Real.hasDerivAt_exp (a.interpret x)) ha'
        simpa [interpret_exp, interpret_mul, Function.comp, mul_comm] using hexp
    | .variable _ | .const _ | .add _ _ | .sub _ _ | .mul _ _ | .div _ _ | .inv _ | .neg _
    | .pow _ _ | .sin _ | .cos _ | .log _ =>
      simp [checkProof] at hcheck
  | log p id ih =>
    match e with
    | .log a =>
      simp only [reconstructDeriv, checkProof, Bool.and_eq_true] at hrec hcheck
      rcases hcheck with ⟨hobl, ha⟩
      match hda : reconstructDeriv a p with
      | none => simp [hda] at hrec
      | some da =>
        simp [hda] at hrec
        subst hrec
        have ha' := ih a da ha hda
        have hpos := obligationPositiveOk_holds obls id a x hobl hdom
        have hne : a.interpret x ≠ 0 := ne_of_gt hpos
        have hlog := HasDerivAt.comp x (Real.hasDerivAt_log hne) ha'
        simpa [interpret_log, interpret_div, Function.comp, div_eq_mul_inv, mul_comm] using hlog
    | .variable _ | .const _ | .add _ _ | .sub _ _ | .mul _ _ | .div _ _ | .inv _ | .neg _
    | .pow _ _ | .sin _ | .cos _ | .exp _ =>
      simp [checkProof] at hcheck

theorem checkDeriv_reconstruct (c : DerivCertificate) (h : checkDeriv c = true) :
    reconstructDeriv c.source c.proof = some c.derivative := by
  simp only [checkDeriv, Bool.and_eq_true] at h
  -- Left-assoc `&&`: final conjunct is the reconstruct/`decide` match.
  have hrec := h.2
  cases hrec' : reconstructDeriv c.source c.proof with
  | none => simp [hrec'] at hrec
  | some d =>
    simp [hrec', decide_eq_true_eq] at hrec
    exact congrArg some hrec

theorem checkDeriv_checkProof (c : DerivCertificate) (h : checkDeriv c = true) :
    checkProof c.source c.proof c.obligations = true := by
  simp only [checkDeriv, Bool.and_eq_true] at h
  -- `checkProof` is the right conjunct of the prefix before the reconstruct match.
  exact h.1.2

/-- Primary soundness theorem (ME-RV-052). -/
theorem checkDeriv_sound
    (c : DerivCertificate) (x : ℝ)
    (hcheck : checkDeriv c = true)
    (hdom : SatisfiesObligations c.obligations x) :
    HasDerivAt c.source.interpret (c.derivative.interpret x) x := by
  exact reconstructDeriv_sound c.source c.proof c.derivative c.obligations x
    (checkDeriv_checkProof c hcheck) (checkDeriv_reconstruct c hcheck) hdom

/-- Within-domain form. -/
theorem checkDerivWithin_sound
    (c : DerivCertificate) (s : Set ℝ) (x : ℝ)
    (hcheck : checkDeriv c = true)
    (hdom : SatisfiesObligations c.obligations x)
    (_hx : x ∈ s) :
    HasDerivWithinAt c.source.interpret (c.derivative.interpret x) s x :=
  (checkDeriv_sound c x hcheck hdom).hasDerivWithinAt

/-- Antiderivative path: same as derivative of claimed `F`. -/
theorem checkAntideriv_sound
    (c : AntiderivCertificate) (x : ℝ)
    (hcheck : checkAntideriv c = true)
    (hdom : SatisfiesObligations c.obligations x) :
    HasDerivAt c.source.interpret (c.derivative.interpret x) x :=
  checkDeriv_sound c x hcheck hdom

theorem checkODE_asDeriv (c : ODECertificate) (h : checkODE c = true) :
    checkDeriv
      { source := c.solution
        derivative := c.rhs
        proof := c.derivProof
        obligations := c.obligations
        claimsCompleteness := c.claimsCompleteness } = true := by
  -- `checkODE` is `checkDeriv`-shaped prefix ∧ `initialConditionsOk` ∧ reconstruct match.
  simp only [checkODE, checkDeriv, Bool.and_eq_true] at h ⊢
  exact ⟨h.1.1, h.2⟩

/-- ODE candidate soundness (ME-RV-053). -/
theorem checkODE_sound
    (c : ODECertificate)
    (hcheck : checkODE c = true)
    (hdom : ∀ x ∈ c.domain, SatisfiesObligations c.obligations x)
    (hic :
      ∀ ic ∈ c.initialConditions.toList,
        c.solution.interpret (ic.point.interpret 0) = ic.value.interpret 0) :
    CandidateSolvesFirstOrderODE
      c.solution.interpret c.rhs.interpret c.domain
      (c.initialConditions.toList.map InitialCondition.asPair) := by
  refine ⟨?_, ?_⟩
  · intro x hx
    have hderiv := checkODE_asDeriv c hcheck
    exact checkDeriv_sound
      { source := c.solution
        derivative := c.rhs
        proof := c.derivProof
        obligations := c.obligations
        claimsCompleteness := c.claimsCompleteness }
      x hderiv (hdom x hx)
  · intro p hp
    rcases List.mem_map.1 hp with ⟨ic, hicmem, rfl⟩
    simpa [InitialCondition.asPair] using hic ic hicmem

/-- Completeness claims are rejected by the checker. -/
theorem checkDeriv_rejects_completeness (c : DerivCertificate)
    (h : checkDeriv c = true) : c.claimsCompleteness = false := by
  simp [checkDeriv, Bool.and_eq_true] at h
  exact Bool.eq_false_iff.2 (by intro hc; simp [hc] at h)

theorem checkODE_rejects_completeness (c : ODECertificate)
    (h : checkODE c = true) : c.claimsCompleteness = false := by
  simp [checkODE, Bool.and_eq_true] at h
  exact Bool.eq_false_iff.2 (by intro hc; simp [hc] at h)

end MathEvidence.Checkers.AnalyticCalculus
