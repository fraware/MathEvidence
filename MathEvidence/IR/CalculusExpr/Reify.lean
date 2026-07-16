/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.RationalExpr.Reify

namespace MathEvidence.IR.CalculusExpr

/-!
Reification for calculus claims reuses `RationalExpr` reification for expression
trees. Unsupported constructs (transcendentals, conditionals, approx numerals)
are rejected at that boundary.
-/

end MathEvidence.IR.CalculusExpr
