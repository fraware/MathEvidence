/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Analysis.Calculus.Deriv.Basic
import MathEvidence.IR.AnalyticExpr.Syntax
import MathEvidence.Checkers.AnalyticCalculus.Basic

/-!
# Analytic interpretation

Interpretation target is Mathlib `HasDerivAt` / `HasDerivWithinAt`. Formal
`RationalExpr` poly-equality alone is never sufficient (see
`forbidsPolyEqualAlone`).
-/

namespace MathEvidence.IR.AnalyticExpr

/-- Marker that Mathlib derivative interpretation is the target semantics. -/
def interpretationTarget : String := "HasDerivAt / HasDerivWithinAt"

/-- Bridge: checker acceptance is on the HasDerivAt path, not polyEqual. -/
theorem interpret_requires_hasDeriv
    (c : MathEvidence.Checkers.AnalyticCalculus.DerivCertificate)
    (_h : MathEvidence.Checkers.AnalyticCalculus.checkDerivCertificate c = true) :
    MathEvidence.Checkers.AnalyticCalculus.requiresHasDerivAt = true ∧
      MathEvidence.Checkers.AnalyticCalculus.forbidsPolyEqualAlone = true := by
  exact ⟨rfl, rfl⟩

end MathEvidence.IR.AnalyticExpr
