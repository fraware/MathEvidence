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

example : checkDeriv productCert = true := by native_decide

/-- Completeness claim rejected. -/
example : checkDeriv { productCert with claimsCompleteness := true } = false := by native_decide

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

example : checkDeriv quotientCert = true := by native_decide

/-- Missing denominator obligation rejected. -/
example : checkDeriv { quotientCert with obligations := #[] } = false := by native_decide

/-- Power rule. -/
def powCert : DerivCertificate where
  source := .pow (.variable 0) 3
  derivative := .mul (.mul (.const 3) (.pow (.variable 0) 2)) (.const 1)
  proof := .pow 3 .variable

example : checkDeriv powCert = true := by native_decide

/-- Nested sin ∘ id. -/
def sinCert : DerivCertificate where
  source := .sin (.variable 0)
  derivative := .mul (.cos (.variable 0)) (.const 1)
  proof := .sin .variable

example : checkDeriv sinCert = true := by native_decide

/-- Exp. -/
def expCert : DerivCertificate where
  source := .exp (.variable 0)
  derivative := .mul (.exp (.variable 0)) (.const 1)
  proof := .exp .variable

example : checkDeriv expCert = true := by native_decide

/-- Log with positivity obligation. -/
def logCert : DerivCertificate where
  source := .log (.variable 0)
  derivative := .div (.const 1) (.variable 0)
  proof := .log .variable 0
  obligations := #[.positive (.variable 0)]

example : checkDeriv logCert = true := by native_decide

/-- Missing log positivity rejected. -/
example : checkDeriv { logCert with obligations := #[] } = false := by native_decide

/-- Incorrect derivative tree rejected. -/
example : checkDeriv {
  source := .sin (.variable 0)
  derivative := .mul (.cos (.variable 0)) (.const 1)
  proof := .exp .variable
} = false := by native_decide

/-- Correct expression with incorrect claimed derivative rejected. -/
example : checkDeriv {
  source := .sin (.variable 0)
  derivative := .const 0
  proof := .sin .variable
} = false := by native_decide

/-- Multivariate source rejected. -/
example : checkDeriv {
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

example : checkODE odeSq = true := by native_decide

/-- Completeness on ODE rejected. -/
example : checkODE { odeSq with claimsCompleteness := true } = false := by native_decide

/-- Antiderivative of `1` is `x`. -/
def antiderivId : AntiderivCertificate where
  source := .variable 0
  derivative := .const 1
  proof := .variable

example : checkAntideriv antiderivId = true := by native_decide

/-- Concrete Mathlib example retained as documentation. -/
theorem hasDerivAt_sq (x : ℝ) :
    HasDerivAt (fun y : ℝ => y ^ 2) (2 * x) x :=
  (hasDerivAt_id x).pow 2

end MathEvidence.Checkers.AnalyticCalculus.Tests
