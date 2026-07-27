/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.AnalyticExpr.Interpret
import MathEvidence.Checkers.AnalyticCalculus.Soundness

/-!
# Encoding bridge for analytic calculus (ME-RV-050)

Visible home for IR ↔ Mathlib interpretation obligations used by tactics.
-/

namespace MathEvidence.Encoding.Analytic

open MathEvidence.IR.AnalyticExpr
open MathEvidence.Checkers.AnalyticCalculus

/-- Interpretation target marker for assurance docs / scans. -/
def interpretationTarget : String := "HasDerivAt / HasDerivWithinAt / CandidateSolvesFirstOrderODE"

/-- Encoding-side restatement of checker soundness. -/
theorem interpret_checkDeriv_sound
    (c : DerivCertificate) (x : ℝ)
    (hcheck : checkDeriv c = true)
    (hdom : SatisfiesObligations c.obligations x) :
    HasDerivAt c.source.interpret (c.derivative.interpret x) x :=
  checkDeriv_sound c x hcheck hdom

end MathEvidence.Encoding.Analytic
