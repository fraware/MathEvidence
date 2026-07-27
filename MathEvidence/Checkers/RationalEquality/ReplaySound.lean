/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Soundness
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.Checkers.RationalEquality.SpecProp
import MathEvidence.Checkers.RationalEquality.Wire
import MathEvidence.IR.RationalExpr.Eval

/-!
# Rational kernel-replay soundness bridge (Wave 2 / ME-RV-022)

`replaySound` is the theorem-producing authority for rational equality kernel
replay. Proof uses reifier/claim identity hypotheses, `checkBool_sound`, and
denominator condition transport — **not** an independent final `ring` on the
original goal.
-/

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.IR.RationalExpr

/-- Side conditions: every certificate denominator factor (and known assumption)
is defined and nonzero in the evaluation environment. -/
def GoalConditions (c : Claim) (denomFactors : List Expr) (env : Env ℚ) : Prop :=
  ∀ e ∈ denomFactors ++ c.knownAssumptions,
    Defined env e ∧ ∃ v, eval env e = some v ∧ v ≠ 0

/-- Kernel-replay soundness: checker acceptance implies the claim proposition.

Generated replay modules instantiate this after proving `checkBool = true` by
`native_decide` (or an equivalent kernel-checked decision procedure).
Request digest coherence is enforced by the driver / verify-bundle path before
replay; it is not required as an unused hypothesis here. -/
theorem replaySound
    (req : Request)
    (cert : Certificate)
    (hCheck : checkBool req cert = true) :
    Claim.proposition req.claim cert.denomFactors :=
  checkBool_sound req cert hCheck

/-- Same conclusion under an explicit `GoalConditions` packaging. -/
theorem replaySound_conditions
    (req : Request)
    (cert : Certificate)
    (hCheck : checkBool req cert = true)
    (env : Env ℚ)
    (hConditions : GoalConditions req.claim cert.denomFactors env) :
    eval env req.claim.lhs = eval env req.claim.rhs :=
  replaySound req cert hCheck env hConditions

end MathEvidence.Checkers.RationalEquality
