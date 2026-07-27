/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.AnalyticCalculus.Certificate
import MathEvidence.IR.AnalyticExpr.Syntax

/-!
# AnalyticExpr wire helpers (JSON-oriented tags)
-/

namespace MathEvidence.Checkers.AnalyticCalculus.Wire

open MathEvidence.IR.AnalyticExpr
open MathEvidence.Checkers.AnalyticCalculus

/-- Tag string for an expression constructor (adapter wire). -/
def Expr.tag : Expr → String
  | .variable _ => "variable"
  | .const _ => "const"
  | .add _ _ => "add"
  | .sub _ _ => "sub"
  | .mul _ _ => "mul"
  | .div _ _ => "div"
  | .inv _ => "inv"
  | .neg _ => "neg"
  | .pow _ _ => "pow"
  | .sin _ => "sin"
  | .cos _ => "cos"
  | .exp _ => "exp"
  | .log _ => "log"

/-- Tag string for a derivation-tree constructor. -/
def DerivProof.tag : DerivProof → String
  | .variable => "variable"
  | .const => "const"
  | .neg _ => "neg"
  | .add _ _ => "add"
  | .sub _ _ => "sub"
  | .mul _ _ => "mul"
  | .inv _ _ => "inv"
  | .div _ _ _ => "div"
  | .pow _ _ => "pow"
  | .sin _ => "sin"
  | .exp _ => "exp"
  | .log _ _ => "log"

end MathEvidence.Checkers.AnalyticCalculus.Wire
