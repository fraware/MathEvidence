/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.AnalyticExpr.Syntax

/-!
# Verified derivative rule identifiers

Human-readable labels for adapter provenance. The authoritative certificate
shape is the inductive `DerivProof` tree in
`MathEvidence.Checkers.AnalyticCalculus.Certificate`.
-/

namespace MathEvidence.IR.AnalyticExpr.DerivativeRules

inductive RuleId where
  | variable
  | const
  | add
  | sub
  | mul
  | div
  | inv
  | neg
  | pow
  | sin
  | cos
  | exp
  | log
  deriving DecidableEq, Repr, Inhabited

/-- Which rule labels are in scope for the analytic vertical fragment. -/
def supported : List RuleId :=
  [.variable, .const, .add, .sub, .mul, .div, .inv, .neg, .pow, .sin, .cos, .exp,
    .log]

end MathEvidence.IR.AnalyticExpr.DerivativeRules
