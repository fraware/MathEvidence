/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.IdealMembership.Check
import MathEvidence.Checkers.IdealMembership.ReplaySound
import MathEvidence.Checkers.IdealMembership.Wire
import MathEvidence.IR.Polynomial.Syntax

/-!
# Offline fixtures for ideal-membership kernel replay (ME-RV-035 / P0-F)

Hand-written request/certificate pairs used by generated replay modules.
Authority is `replaySound` after `checkBool = true`.

These fixtures back the **release-grade** benchmark tier. The in-repo
`held_out` stratum remains synthetic; external library-derived held-out
(ME-RV-081) stays BLOCKED(human).
-/

namespace MathEvidence.Checkers.IdealMembership.OfflineFixtures

open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership

/-- `xy ∈ ⟨x, y⟩` via multipliers `(y, 0)`. -/
def claim_xy : Claim 2 where
  target := ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [1, 1] }]⟩
  generators := #[
    ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [1, 0] }]⟩,
    ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [0, 1] }]⟩]

def req_xy : Request 2 := Request.ofClaim! claim_xy

def cert_xy : Certificate 2 where
  requestDigest := req_xy.requestDigest
  multipliers := #[
    ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [0, 1] }]⟩,
    SparsePoly.zero 2]

theorem replay_xy : checkBool req_xy cert_xy = true := by native_decide

theorem replay_xy_sound : Claim.proposition req_xy.claim :=
  replaySound req_xy cert_xy replay_xy

/-- `x² - 1 ∈ ⟨x - 1⟩` via multiplier `x + 1`. -/
def claim_x2m1 : Claim 1 where
  target := ⟨[
    { coefficient := 1, monomial := Monomial.ofList! 1 [2] },
    { coefficient := -1, monomial := Monomial.ofList! 1 [0] }]⟩
  generators := #[⟨[
    { coefficient := 1, monomial := Monomial.ofList! 1 [1] },
    { coefficient := -1, monomial := Monomial.ofList! 1 [0] }]⟩]

def req_x2m1 : Request 1 := Request.ofClaim! claim_x2m1

def cert_x2m1 : Certificate 1 where
  requestDigest := req_x2m1.requestDigest
  multipliers := #[⟨[
    { coefficient := 1, monomial := Monomial.ofList! 1 [1] },
    { coefficient := 1, monomial := Monomial.ofList! 1 [0] }]⟩]

theorem replay_x2m1 : checkBool req_x2m1 cert_x2m1 = true := by native_decide

theorem replay_x2m1_sound : Claim.proposition req_x2m1.claim :=
  replaySound req_x2m1 cert_x2m1 replay_x2m1

end MathEvidence.Checkers.IdealMembership.OfflineFixtures
