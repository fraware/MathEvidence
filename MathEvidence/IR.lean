/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.Common.Identifier
import MathEvidence.IR.RationalExpr.Syntax
import MathEvidence.IR.RationalExpr.Eval
import MathEvidence.IR.RationalExpr.Poly
import MathEvidence.IR.RationalExpr.PolyCompute
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
import MathEvidence.IR.FormalRationalCalculus
import MathEvidence.IR.AnalyticExpr.Syntax
import MathEvidence.IR.Polynomial.Syntax

/-!
# MathEvidence.IR

Typed, restricted mathematical languages and their Lean semantics.

Domain IRs:

* `RationalExpr` (RFC 0001)
* `MatrixExpr` (exact linear algebra, Milestone 2)
* `FinitePredicate` (finite counterexamples, Milestone 2)
* `FormalRationalCalculus` (formal rational differentiation/substitution identities,
  formerly `CalculusExpr`; not analytic semantics)
* `AnalyticExpr` (analytic-calculus syntax scaffold, ME-105)
* `Polynomial` (sparse polynomial syntax for ideal-membership federation scaffolding)
-/
