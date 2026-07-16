/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.CalculusExpr.Ops
import MathEvidence.IR.RationalExpr.Soundness

namespace MathEvidence.IR.CalculusExpr

open MathEvidence.IR.RationalExpr

/-!
# Soundness notes (Milestone 5)

`exprEqual` / `polyEqual` establish rational-function identity of formal
derivatives and substitutions. This is **candidate verification**, not:

* completeness of antiderivatives;
* uniqueness of ODE solutions;
* that a recurrence determines a unique sequence;
* analytic differentiability beyond the rational fragment.

Branch and singularity obligations remain the explicit `domainConditions` list.
-/

theorem exprEqual_of_polyEqual (a b : Expr) (h : polyEqual a b = true) :
    exprEqual a b = true := h

theorem derivativeOk_implies_exprEqual (xIdx : Nat) (f g : Expr)
    (h : derivativeOk xIdx f g = true) :
    exprEqual (formalDeriv xIdx f) g = true := h

theorem antiderivativeOk_implies_exprEqual (xIdx : Nat) (f F : Expr)
    (h : antiderivativeOk xIdx f F = true) :
    exprEqual (formalDeriv xIdx F) f = true := h

end MathEvidence.IR.CalculusExpr
