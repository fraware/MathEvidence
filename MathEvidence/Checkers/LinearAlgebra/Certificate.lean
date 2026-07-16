/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.EvidenceId
import MathEvidence.IR.MatrixExpr.Syntax

namespace MathEvidence.Checkers.LinearAlgebra

open MathEvidence.Core
open MathEvidence.IR.MatrixExpr

/-- Untrusted certificate for exact linear algebra.

The backend does **not** supply a trusted Boolean. Lean recomputes matrix
products / determinants over `ℚ`. -/
structure Certificate where
  requestDigest : RequestDigest
  /-- Inverse matrix for `inverseWitness`. -/
  inverse : Option Matrix := none
  /-- Solution or kernel vector for system / kernel operations. -/
  vector : Option Vector := none
  deriving DecidableEq, Repr, Inhabited

/-- Optional informational candidate (checker recomputes all equalities). -/
structure Candidate where
  reportedOk : Bool := true
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.Checkers.LinearAlgebra
