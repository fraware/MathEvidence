/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.EvidenceId
import MathEvidence.IR.FinitePredicate.Syntax

namespace MathEvidence.Checkers.Counterexample

open MathEvidence.Core
open MathEvidence.IR.FinitePredicate

/-- Untrusted finite counterexample certificate.

Lean re-evaluates the original predicate at `witness`; the backend Boolean is
never trusted. -/
structure Certificate where
  requestDigest : RequestDigest
  /-- Typed assignment, one value per claim domain variable. -/
  witness : Assignment
  deriving DecidableEq, Repr, Inhabited

structure Candidate where
  reportedFalse : Bool := true
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.Checkers.Counterexample
