/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Checkers.RationalEquality.ReplaySound
import MathEvidence.IR.RationalExpr.Eval

/-!
# Rational equality Mathlib bridge (ME-RV-023)

Transport from `Claim.proposition` / `replaySound` to a concrete `ℚ` equality.

Proof *authority* is always `replaySound` / `checkBool_sound`. Side conditions
may use local hypotheses. An independent final `field_simp; ring` is **not**
authority.
-/

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.IR.RationalExpr
open MathEvidence.Checkers.RationalEquality.OfflineFixtures

/-- `Claim.proposition` + eval witnesses ⇒ Mathlib equality on `ℚ`. -/
theorem eq_of_proposition
    {c : Claim} {conds : List Expr}
    (hProp : Claim.proposition c conds)
    (env : Env ℚ)
    (hConds :
      ∀ e ∈ conds ++ c.knownAssumptions,
        Defined env e ∧ ∃ v, eval env e = some v ∧ v ≠ 0)
    {L R : ℚ}
    (hL : eval env c.lhs = some L)
    (hR : eval env c.rhs = some R) :
    L = R := by
  have hEq : eval env c.lhs = eval env c.rhs := hProp env hConds
  rw [hL, hR] at hEq
  exact Option.some.inj hEq

/-- Same transport with `replaySound` as the named authority. -/
theorem eq_of_replaySound
    (req : Request) (cert : Certificate)
    (hCheck : checkBool req cert = true)
    (env : Env ℚ)
    (hConds : GoalConditions req.claim cert.denomFactors env)
    {L R : ℚ}
    (hL : eval env req.claim.lhs = some L)
    (hR : eval env req.claim.rhs = some R) :
    L = R :=
  eq_of_proposition (replaySound req cert hCheck) env hConds hL hR

/-- Alias emphasizing `checkBool_sound` as the checker theorem. -/
theorem eq_of_checkBool_sound
    (req : Request) (cert : Certificate)
    (hCheck : checkBool req cert = true)
    (env : Env ℚ)
    (hConds : GoalConditions req.claim cert.denomFactors env)
    {L R : ℚ}
    (hL : eval env req.claim.lhs = some L)
    (hR : eval env req.claim.rhs = some R) :
    L = R :=
  eq_of_replaySound req cert hCheck env hConds hL hR

private def env1 (x : ℚ) : Env ℚ := fun i => List.getD [x] i 0

private theorem claim_eq_basic_sympy :
    req_basic_sympy.claim = claim_basic_sympy := by native_decide

private theorem claim_eq_basic_mathematica :
    req_basic_mathematica.claim = claim_basic_mathematica := by native_decide

private theorem claim_eq_valid_identity :
    req_valid_identity.claim = claim_valid_identity := by native_decide

private theorem eval_add_var_int (x : ℚ) :
    eval (env1 x) (Expr.add (Expr.var 0) (Expr.int 1)) = some (x + 1) := by
  simp [eval, env1, List.getD]

private theorem eval_classic_div (x : ℚ) (hx : x - 1 ≠ 0) :
    eval (env1 x)
      (Expr.div
        (Expr.sub (Expr.pow (Expr.var 0) 2) (Expr.int 1))
        (Expr.sub (Expr.var 0) (Expr.int 1))) =
      some ((x ^ 2 - 1) / (x - 1)) := by
  simp only [eval, env1, List.getD]
  have : ¬((x - 1 : ℚ) = 0) := hx
  simp [this]

private theorem conds_classic (x : ℚ) (hx : x - 1 ≠ 0) (c : Claim)
    (hc : c.knownAssumptions = [])
    (conds : List Expr)
    (hd : conds = [Expr.sub (Expr.var 0) (Expr.int 1)]) :
    ∀ e ∈ conds ++ c.knownAssumptions,
      Defined (env1 x) e ∧ ∃ v, eval (env1 x) e = some v ∧ v ≠ 0 := by
  intro e he
  rw [hd, hc, List.append_nil, List.mem_singleton] at he
  subst he
  refine ⟨by simp [Defined, eval, env1, List.getD], ?_⟩
  exact ⟨x - 1, by simp [eval, env1, List.getD], hx⟩

/-- Protocol-reference identity closed by fixture `sound_basic_sympy` (authority). -/
theorem close_basic_identity (x : ℚ) (hx : x - 1 ≠ 0) :
    (x ^ 2 - 1) / (x - 1) = x + 1 := by
  have hProp : Claim.proposition claim_basic_sympy cert_basic_sympy.denomFactors := by
    simpa [claim_eq_basic_sympy] using sound_basic_sympy
  refine eq_of_proposition hProp (env1 x) ?hConds ?hL ?hR
  · exact conds_classic x hx claim_basic_sympy rfl cert_basic_sympy.denomFactors rfl
  · simpa [claim_basic_sympy] using eval_classic_div x hx
  · simpa [claim_basic_sympy] using eval_add_var_int x

/-- Same identity via Mathematica offline fixture soundness theorem. -/
theorem close_basic_identity_mathematica (x : ℚ) (hx : x - 1 ≠ 0) :
    (x ^ 2 - 1) / (x - 1) = x + 1 := by
  have hProp :
      Claim.proposition claim_basic_mathematica cert_basic_mathematica.denomFactors := by
    simpa [claim_eq_basic_mathematica] using sound_basic_mathematica
  refine eq_of_proposition hProp (env1 x) ?hConds ?hL ?hR
  · exact conds_classic x hx claim_basic_mathematica rfl
      cert_basic_mathematica.denomFactors rfl
  · simpa [claim_basic_mathematica] using eval_classic_div x hx
  · simpa [claim_basic_mathematica] using eval_add_var_int x

/-- Valid-identity conformance fixture (same IR as basic). -/
theorem close_valid_identity (x : ℚ) (hx : x - 1 ≠ 0) :
    (x ^ 2 - 1) / (x - 1) = x + 1 := by
  have hProp :
      Claim.proposition claim_valid_identity cert_valid_identity.denomFactors := by
    simpa [claim_eq_valid_identity] using sound_valid_identity
  refine eq_of_proposition hProp (env1 x) ?hConds ?hL ?hR
  · exact conds_classic x hx claim_valid_identity rfl cert_valid_identity.denomFactors rfl
  · simpa [claim_valid_identity] using eval_classic_div x hx
  · simpa [claim_valid_identity] using eval_add_var_int x

/-! ## Non-fixture live Bridge (ME-RV-023 / E-12)

These claims are **not** protocol-reference offline fixtures. Authority is still
`eq_of_replaySound` / `checkBool_sound` — never an independent final `ring`.
-/

/-- Non-fixture claim: `x + 0 = x`. -/
def claim_live_add0 : Claim where
  varNames := ["x"]
  lhs := .add (.var 0) (.int 0)
  rhs := .var 0

def req_live_add0 : Request := Request.ofClaim! claim_live_add0

def cert_live_add0 : Certificate where
  requestDigest := req_live_add0.requestDigest
  denomFactors := []

theorem check_live_add0 : checkBool req_live_add0 cert_live_add0 = true := by
  native_decide

private theorem claim_eq_live_add0 : req_live_add0.claim = claim_live_add0 := by
  native_decide

private theorem eval_add0_lhs (x : ℚ) :
    eval (env1 x) claim_live_add0.lhs = some (x + 0) := by
  simp [eval, env1, List.getD, claim_live_add0]

private theorem eval_add0_rhs (x : ℚ) :
    eval (env1 x) claim_live_add0.rhs = some x := by
  simp [eval, env1, List.getD, claim_live_add0]

/-- Non-fixture identity closed by elaborated live `eq_of_replaySound`. -/
theorem close_live_add0 (x : ℚ) : x + 0 = x := by
  have hProp : Claim.proposition claim_live_add0 cert_live_add0.denomFactors := by
    simpa [claim_eq_live_add0] using
      (checkBool_sound req_live_add0 cert_live_add0 check_live_add0)
  refine eq_of_proposition hProp (env1 x) ?hConds ?hL ?hR
  · intro e he
    simp [cert_live_add0, claim_live_add0] at he
  · exact eval_add0_lhs x
  · exact eval_add0_rhs x

/-- Non-fixture claim: `(x * y) / y = x` with denom factor `y`. -/
def claim_live_cancel : Claim where
  varNames := ["x", "y"]
  lhs := .div (.mul (.var 0) (.var 1)) (.var 1)
  rhs := .var 0

def req_live_cancel : Request := Request.ofClaim! claim_live_cancel

def cert_live_cancel : Certificate where
  requestDigest := req_live_cancel.requestDigest
  denomFactors := [.var 1]

theorem check_live_cancel : checkBool req_live_cancel cert_live_cancel = true := by
  native_decide

private theorem claim_eq_live_cancel : req_live_cancel.claim = claim_live_cancel := by
  native_decide

private def env2 (x y : ℚ) : Env ℚ := fun i => List.getD [x, y] i 0

private theorem eval_cancel_lhs (x y : ℚ) (hy : y ≠ 0) :
    eval (env2 x y) claim_live_cancel.lhs = some ((x * y) / y) := by
  simp only [eval, env2, List.getD, claim_live_cancel]
  have : ¬(y = 0) := hy
  simp [this]

private theorem eval_cancel_rhs (x y : ℚ) :
    eval (env2 x y) claim_live_cancel.rhs = some x := by
  simp [eval, env2, List.getD, claim_live_cancel]

/-- Non-fixture cancel identity; `hy` discharges Bridge side conditions only. -/
theorem close_live_cancel (x y : ℚ) (hy : y ≠ 0) : (x * y) / y = x := by
  have hProp : Claim.proposition claim_live_cancel cert_live_cancel.denomFactors := by
    simpa [claim_eq_live_cancel] using
      (checkBool_sound req_live_cancel cert_live_cancel check_live_cancel)
  refine eq_of_proposition hProp (env2 x y) ?hConds ?hL ?hR
  · intro e he
    simp [cert_live_cancel, claim_live_cancel] at he
    subst he
    refine ⟨by simp [Defined, eval, env2, List.getD], ?_⟩
    exact ⟨y, by simp [eval, env2, List.getD], hy⟩
  · exact eval_cancel_lhs x y hy
  · exact eval_cancel_rhs x y

/-- Adversarial: wrong digest never reaches Bridge authority. -/
theorem adversarial_live_wrong_digest_rejected :
    checkBool req_live_add0
      { requestDigest :=
          ⟨"sha256:0000000000000000000000000000000000000000000000000000000000000000"⟩
        denomFactors := [] } = false := by
  native_decide

/-- Adversarial: missing denom coverage rejected before Bridge. -/
theorem adversarial_live_missing_denom_rejected :
    checkBool req_live_cancel
      { requestDigest := req_live_cancel.requestDigest, denomFactors := [] } = false := by
  native_decide

end MathEvidence.Checkers.RationalEquality
