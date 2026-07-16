/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.Common.Identifier
import MathEvidence.IR.RationalExpr.Syntax
import MathEvidence.IR.RationalExpr.Eval
import MathEvidence.IR.RationalExpr.Poly
import MathEvidence.IR.RationalExpr.Reify
import MathEvidence.IR.RationalExpr.Soundness
import MathEvidence.IR.RationalExpr.Serialize
import MathEvidence.IR.RationalExpr.Wire
import MathEvidence.IR.MatrixExpr.Syntax
import MathEvidence.IR.MatrixExpr.Eval
import MathEvidence.IR.MatrixExpr.Ops
import MathEvidence.IR.MatrixExpr.Reify
import MathEvidence.IR.MatrixExpr.Soundness
import MathEvidence.IR.MatrixExpr.Serialize
import MathEvidence.IR.FinitePredicate.Syntax
import MathEvidence.IR.FinitePredicate.Eval
import MathEvidence.IR.FinitePredicate.Reify
import MathEvidence.IR.FinitePredicate.Soundness
import MathEvidence.IR.FinitePredicate.Serialize
import MathEvidence.IR.CalculusExpr.Syntax
import MathEvidence.IR.CalculusExpr.Ops
import MathEvidence.IR.CalculusExpr.Eval
import MathEvidence.IR.CalculusExpr.Serialize
import MathEvidence.IR.CalculusExpr.Soundness
import MathEvidence.IR.CalculusExpr.Reify

/-!
# MathEvidence.IR

Typed, restricted mathematical languages and their Lean semantics.

Domain IRs:

* `RationalExpr` (RFC 0001)
* `MatrixExpr` (exact linear algebra, Milestone 2)
* `FinitePredicate` (finite counterexamples, Milestone 2)
* `CalculusExpr` (symbolic calculus candidates, Milestone 5)
-/
