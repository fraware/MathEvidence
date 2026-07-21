/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.EvidenceId
import MathEvidence.IR.RationalExpr.Syntax

/-!
# Rational equality request / claim structures

Structures only — no Mathlib `ℚ` evaluation. Propositional soundness lives in
`SpecProp.lean` so Lake exes can import Spec without linking Mathlib.
-/

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.Core
open MathEvidence.IR.RationalExpr

/-- Mathematical claim: equality of two rational expressions under explicit
nonzero conditions on a listed set of denominator factors (RFC 0001).

The claim is *not* identity of totalized field expressions at poles. -/
structure Claim where
  /-- Canonical variable names (index order). -/
  varNames : List String
  lhs : Expr
  rhs : Expr
  /-- Assumptions already available in the local context (nonzero obligations). -/
  knownAssumptions : List Expr := []
  /-- Requested claim strength (Milestone 1: `soundResult`). -/
  claimClass : ClaimClass := .soundResult
  deriving DecidableEq, Repr, Inhabited

/-- Versioned request binding digest + claim. -/
structure Request where
  capability : CapabilityRef := .rationalEquality
  claim : Claim
  /-- Precomputed or recomputed request digest. -/
  requestDigest : RequestDigest
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.Checkers.RationalEquality
