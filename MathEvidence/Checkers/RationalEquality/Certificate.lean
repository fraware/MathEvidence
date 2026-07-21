/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.EvidenceId
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.Core
open MathEvidence.IR.RationalExpr

/-- Untrusted certificate for rational equality (solver-independent).

The backend does **not** supply a trusted Boolean. Lean recomputes the polynomial
identity and definedness obligations. -/
structure Certificate where
  /-- Must match the request digest exactly. -/
  requestDigest : RequestDigest
  /-- Denominator factors whose nonzero status is required for the derivation. -/
  denomFactors : List Expr
  deriving DecidableEq, Repr, Inhabited

/-- Candidate output is diagnostic only for equality claims; equality is recomputed
from the claim and certificate. -/
structure Candidate where
  /-- Diagnostic backend report about the normalized numerator of `lhs - rhs`.
  The checker does not trust this bit; it recomputes `differenceNumerator` via
  `polyOk`. -/
  reportedNumeratorZero : Bool := true
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.Checkers.RationalEquality
