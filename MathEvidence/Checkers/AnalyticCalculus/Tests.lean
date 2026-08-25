/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.AnalyticCalculus.Soundness

/-!
# Analytic calculus checker tests (ME-RV-050..053)
-/

namespace MathEvidence.Checkers.AnalyticCalculus.Tests

open MathEvidence.IR.AnalyticExpr
open MathEvidence.Checkers.AnalyticCalculus

/-- Product rule: `(x * x)' = 1*x + x*1`. -/
def productCert : DerivCertificate where
  source := .mul (.variable 0) (.variable 0)
  derivative := .add (.mul (.const 1) (.variable 0)) (.mul (.variable 0) (.const 1))
  proof := .mul .variable .variable

theorem productCert_ok : checkDeriv productCert = true := by native_decide

/-- Completeness claim rejected. -/
theorem productCert_completeness_rejected :
    checkDeriv { productCert with claimsCompleteness := true } = false := by
  native_decide

/-- Quotient with explicit nonzero obligation. -/
def quotientCert : DerivCertificate where
  source := .div (.variable 0) (.add (.variable 0) (.const 1))
  derivative :=
    .div
      (.sub (.mul (.const 1) (.add (.variable 0) (.const 1)))
        (.mul (.variable 0) (.const 1)))
      (.mul (.add (.variable 0) (.const 1)) (.add (.variable 0) (.const 1)))
  proof := .div .variable (.add .variable .const) 0
  obligations := #[.nonzero (.add (.variable 0) (.const 1))]

/- Lean 4.14.0 `native_decide`/`ofReduceBool` is ill-typed on this certificate
(`Eq.refl true` vs `reduceBool _ = true`). The VM check still fails the build
if `checkDeriv` does not accept the fixture. -/
#eval
  if checkDeriv quotientCert then ()
  else panic! "expected checkDeriv quotientCert = true"

/-- Missing denominator obligation rejected. -/
theorem quotientCert_missing_obligation_rejected :
    checkDeriv { quotientCert with obligations := #[] } = false := by
  native_decide

/-- Power rule. -/
def powCert : DerivCertificate where
  source := .pow (.variable 0) 3
  derivative := .mul (.mul (.const 3) (.pow (.variable 0) 2)) (.const 1)
  proof := .pow 3 .variable

theorem powCert_ok : checkDeriv powCert = true := by native_decide

/-- Nested sin ∘ id. -/
def sinCert : DerivCertificate where
  source := .sin (.variable 0)
  derivative := .mul (.cos (.variable 0)) (.const 1)
  proof := .sin .variable

theorem sinCert_ok : checkDeriv sinCert = true := by native_decide

/-- Exp. -/
def expCert : DerivCertificate where
  source := .exp (.variable 0)
  derivative := .mul (.exp (.variable 0)) (.const 1)
  proof := .exp .variable

theorem expCert_ok : checkDeriv expCert = true := by native_decide

/-- Log with positivity obligation. -/
def logCert : DerivCertificate where
  source := .log (.variable 0)
  derivative := .div (.const 1) (.variable 0)
  proof := .log .variable 0
  obligations := #[.positive (.variable 0)]

theorem logCert_ok : checkDeriv logCert = true := by native_decide

/-- Missing log positivity rejected. -/
theorem logCert_missing_obligation_rejected :
    checkDeriv { logCert with obligations := #[] } = false := by
  native_decide

/-- Incorrect derivative tree rejected. -/
theorem sinCert_wrong_proof_rejected : checkDeriv {
  source := .sin (.variable 0)
  derivative := .mul (.cos (.variable 0)) (.const 1)
  proof := .exp .variable
} = false := by native_decide

/-- Correct expression with incorrect claimed derivative rejected. -/
theorem sinCert_wrong_derivative_rejected : checkDeriv {
  source := .sin (.variable 0)
  derivative := .const 0
  proof := .sin .variable
} = false := by native_decide

/-- Multivariate source rejected. -/
theorem multivariate_source_rejected : checkDeriv {
  source := .variable 1
  derivative := .const 0
  proof := .variable
} = false := by native_decide

/-- ODE residual for `y = x^2`, `y' = 2x` (as mul form). -/
def odeSq : ODECertificate where
  solution := .pow (.variable 0) 2
  rhs := .mul (.mul (.const 2) (.pow (.variable 0) 1)) (.const 1)
  derivProof := .pow 2 .variable
  initialConditions := #[{ point := .const 0, value := .const 0 }]

theorem odeSq_ok : checkODE odeSq = true := by native_decide

/-- Completeness on ODE rejected. -/
theorem odeSq_completeness_rejected :
    checkODE { odeSq with claimsCompleteness := true } = false := by
  native_decide

/-- Antiderivative of `1` is `x`. -/
def antiderivId : AntiderivCertificate where
  source := .variable 0
  derivative := .const 1
  proof := .variable

theorem antiderivId_ok : checkAntideriv antiderivId = true := by native_decide

/-- Concrete Mathlib example retained as documentation. -/
theorem hasDerivAt_sq (x : ℝ) :
    HasDerivAt (fun y : ℝ => y ^ 2) (2 * x) x := by
  simpa [id_eq, pow_two, pow_one, Nat.cast_eq_ofNat, mul_one, mul_comm,
    mul_left_comm, mul_assoc] using
    (HasDerivAt.pow (n := 2) (hasDerivAt_id (𝕜 := ℝ) x))

end MathEvidence.Checkers.AnalyticCalculus.Tests
