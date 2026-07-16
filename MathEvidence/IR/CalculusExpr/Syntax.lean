/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.IR.CalculusExpr

open MathEvidence.IR.RationalExpr (Expr)

/-!
# CalculusExpr

Univariate / low-arity rational expressions for Milestone 5 symbolic calculus.
Syntax reuses `RationalExpr.Expr`. Domain / singularity / branch conditions are
always listed explicitly on claims; candidate validity never implies completeness.
-/

/-- Supported calculus claim operations. -/
inductive Operation where
  | derivativeCandidate
  | antiderivativeCandidate
  | recurrenceIdentity
  | odeCandidate
  deriving DecidableEq, Repr, Inhabited

def Operation.toWire : Operation → String
  | .derivativeCandidate => "derivative_candidate"
  | .antiderivativeCandidate => "antiderivative_candidate"
  | .recurrenceIdentity => "recurrence_identity"
  | .odeCandidate => "ode_candidate"

def Operation.ofWire? : String → Option Operation
  | "derivative_candidate" => some .derivativeCandidate
  | "antiderivative_candidate" => some .antiderivativeCandidate
  | "recurrence_identity" => some .recurrenceIdentity
  | "ode_candidate" => some .odeCandidate
  | _ => none

/-- Initial condition `y(point) = value` (rational expressions). -/
structure InitialCondition where
  point : Expr
  value : Expr
  deriving DecidableEq, Repr, Inhabited

def defaultSizeLimit : Nat := 10000

/-- Cover check: every denominator subexpression appears in the explicit condition list. -/
def densCovered (e : Expr) (conds : List Expr) : Bool :=
  e.denominators.all fun d => conds.contains d

/-- All expressions within size limit. -/
def exprsWithinLimit (es : List Expr) (limit : Nat := defaultSizeLimit) : Bool :=
  es.all (·.withinSizeLimit limit)

end MathEvidence.IR.CalculusExpr
