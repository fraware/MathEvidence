/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.AnalyticExpr.Syntax

/-!
# Verified derivative rule table

CAS proposes candidates; Lean builds proofs from these rules. No completeness.
-/

namespace MathEvidence.IR.AnalyticExpr.DerivativeRules

inductive RuleId where
  | const
  | add
  | sub
  | mul
  | div
  | neg
  | pow
  | sin
  | exp
  | log
  deriving DecidableEq, Repr, Inhabited

/-- Which rules are in scope for the analytic vertical fragment. -/
def supported : List RuleId :=
  [.const, .add, .sub, .mul, .div, .neg, .pow, .sin, .exp, .log]

end MathEvidence.IR.AnalyticExpr.DerivativeRules
