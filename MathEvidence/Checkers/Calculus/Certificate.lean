/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.EvidenceId
import MathEvidence.IR.CalculusExpr.Syntax
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.Checkers.Calculus

open MathEvidence.Core
open MathEvidence.IR.CalculusExpr
open MathEvidence.IR.RationalExpr (Expr)

/-- Untrusted calculus certificate.

Lean re-runs formal differentiation / substitution; backend Booleans are never
trusted. Optional fields mirror the request when the adapter echoes them.
-/
structure Certificate where
  requestDigest : RequestDigest
  /-- Echo of operation for malformed-evidence rejection. -/
  operation : Operation
  /-- Explicit domain conditions (must match request coverage obligations). -/
  domainConditions : List Expr := []
  deriving DecidableEq, Repr, Inhabited

structure Candidate where
  /-- Backend-reported success hint; never trusted. -/
  reportedOk : Bool := true
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.Checkers.Calculus
