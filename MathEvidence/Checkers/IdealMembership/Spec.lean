/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.Digest.Types
import MathEvidence.IR.Polynomial.Syntax
import MathEvidence.IR.Polynomial.Normalize

/-!
# Ideal-membership claim / request (ME-RV-032)

Witness claim only: `f ∈ Ideal.span (range g)` via multipliers `q` with
`f = ∑ qᵢ · gᵢ`. No Gröbner / radical / equality claims.
-/

namespace MathEvidence.Checkers.IdealMembership

open MathEvidence.Core
open MathEvidence.IR.Polynomial

inductive ClaimClass where
  | witness
  | candidate
  | soundResult
  deriving DecidableEq, Repr, Inhabited

structure CapabilityRef where
  id : String := "algebra.ideal_membership_witness"
  version : String := "0.1.0"
  deriving DecidableEq, Repr, Inhabited

structure ResourcePolicy where
  maxVariableCount : Nat := 64
  maxGeneratorCount : Nat := 256
  maxTermCount : Nat := 4096
  maxExponent : Nat := 64
  maxCoefficientDigits : Nat := 4096
  deriving DecidableEq, Repr, Inhabited

def defaultResourcePolicy : ResourcePolicy := {}

structure Claim (m : Nat) where
  target : SparsePoly m
  generators : Array (SparsePoly m)
  claimClass : ClaimClass := .witness
  deriving DecidableEq, Repr, Inhabited

structure Request (m : Nat) where
  capability : CapabilityRef := {}
  claim : Claim m
  resourcePolicy : ResourcePolicy := defaultResourcePolicy
  requestDigest : RequestDigest
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.Checkers.IdealMembership
