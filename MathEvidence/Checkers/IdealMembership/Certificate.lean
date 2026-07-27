/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.Digest.Types
import MathEvidence.IR.Polynomial.Syntax
import MathEvidence.Checkers.IdealMembership.Spec

/-!
# Ideal-membership certificate
-/

namespace MathEvidence.Checkers.IdealMembership

open MathEvidence.Core
open MathEvidence.IR.Polynomial

structure Certificate (m : Nat) where
  requestDigest : RequestDigest
  multipliers : Array (SparsePoly m)
  deriving DecidableEq, Repr, Inhabited

/-- Concrete witness package (target + generators + multipliers). -/
structure MembershipWitness (m : Nat) where
  target : SparsePoly m
  generators : Array (SparsePoly m)
  multipliers : Array (SparsePoly m)
  deriving DecidableEq, Repr

end MathEvidence.Checkers.IdealMembership
