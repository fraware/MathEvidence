/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.LinearAlgebra.Check
import MathEvidence.Checkers.LinearAlgebra.Replay
import MathEvidence.Checkers.LinearAlgebra.Soundness
import MathEvidence.IR.MatrixExpr.Syntax

namespace MathEvidence.Checkers.LinearAlgebra.Tests

open MathEvidence.IR.MatrixExpr
open MathEvidence.Checkers.LinearAlgebra

/-!
Hand-written offline fixtures for inverse, system, kernel, and det identity.
-/

/-- `[[2,0],[0,1/2]]` inverse of `[[1/2,0],[0,2]]`. -/
def A_diag : Matrix :=
  { nrows := 2, ncols := 2
    entries := [[⟨1, 2⟩, RatLit.ofInt 0], [RatLit.ofInt 0, RatLit.ofInt 2]] }

def B_diag : Matrix :=
  { nrows := 2, ncols := 2
    entries := [[RatLit.ofInt 2, RatLit.ofInt 0], [RatLit.ofInt 0, ⟨1, 2⟩]] }

def claim_inv : Claim where
  operation := .inverseWitness
  matrix := A_diag
  claimClass := .witness

def req_inv : Request := Request.ofClaim claim_inv

def cert_inv : Certificate where
  requestDigest := req_inv.requestDigest
  inverse := some B_diag

/-- System `[[1,1],[0,1]] [x,y]^T = [3,2]^T` → `[1,2]`. -/
def A_sys : Matrix :=
  { nrows := 2, ncols := 2
    entries :=
      [[RatLit.ofInt 1, RatLit.ofInt 1],
       [RatLit.ofInt 0, RatLit.ofInt 1]] }

def b_sys : Vector := [RatLit.ofInt 3, RatLit.ofInt 2]
def x_sys : Vector := [RatLit.ofInt 1, RatLit.ofInt 2]

def claim_sys : Claim where
  operation := .systemSolution
  matrix := A_sys
  rhs := b_sys
  claimClass := .witness

def req_sys : Request := Request.ofClaim claim_sys

def cert_sys : Certificate where
  requestDigest := req_sys.requestDigest
  vector := some x_sys

/-- Kernel of `[[1,2],[2,4]]`: vector `[2,-1]`. -/
def A_ker : Matrix :=
  { nrows := 2, ncols := 2
    entries :=
      [[RatLit.ofInt 1, RatLit.ofInt 2],
       [RatLit.ofInt 2, RatLit.ofInt 4]] }

def v_ker : Vector := [RatLit.ofInt 2, RatLit.ofInt (-1)]

def claim_ker : Claim where
  operation := .kernelVector
  matrix := A_ker
  claimClass := .witness

def req_ker : Request := Request.ofClaim claim_ker

def cert_ker : Certificate where
  requestDigest := req_ker.requestDigest
  vector := some v_ker

/-- `det [[1,2],[3,4]] = -2`. -/
def A_det : Matrix :=
  { nrows := 2, ncols := 2
    entries :=
      [[RatLit.ofInt 1, RatLit.ofInt 2],
       [RatLit.ofInt 3, RatLit.ofInt 4]] }

def claim_det : Claim where
  operation := .detIdentity
  matrix := A_det
  claimedDet := some (RatLit.ofInt (-2))
  claimClass := .soundResult

def req_det : Request := Request.ofClaim claim_det

def cert_det : Certificate where
  requestDigest := req_det.requestDigest

/-- Wrong inverse must be rejected. -/
def B_bad : Matrix := Matrix.identity 2

def cert_inv_bad : Certificate where
  requestDigest := req_inv.requestDigest
  inverse := some B_bad

/-- Digest mismatch rejected. -/
def cert_bad_digest : Certificate where
  requestDigest := ⟨"sha256:0000000000000000000000000000000000000000000000000000000000000000"⟩
  inverse := some B_diag

/-- Zero vector is not a kernel witness. -/
def cert_ker_zero : Certificate where
  requestDigest := req_ker.requestDigest
  vector := some (Vector.zero 2)

theorem replay_inv :
    checkBool req_inv cert_inv = true := by native_decide

theorem replay_sys :
    checkBool req_sys cert_sys = true := by native_decide

theorem replay_ker :
    checkBool req_ker cert_ker = true := by native_decide

theorem replay_det :
    checkBool req_det cert_det = true := by native_decide

theorem reject_bad_inverse :
    checkBool req_inv cert_inv_bad = false := by native_decide

theorem reject_bad_digest :
    checkBool req_inv cert_bad_digest = false := by native_decide

theorem reject_zero_kernel :
    checkBool req_ker cert_ker_zero = false := by native_decide

theorem replay_report_inv :
    (replay { request := req_inv, certificate := cert_inv }).accepted = true := by
  native_decide

theorem sound_inv :
    Claim.proposition claim_inv cert_inv.inverse cert_inv.vector :=
  checkBool_sound req_inv cert_inv replay_inv

theorem sound_ker :
    Claim.proposition claim_ker cert_ker.inverse cert_ker.vector :=
  checkBool_sound req_ker cert_ker replay_ker

end MathEvidence.Checkers.LinearAlgebra.Tests
