/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.Replay
import MathEvidence.Checkers.RationalEquality.Soundness
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.Checkers.RationalEquality.Tests

open MathEvidence.IR.RationalExpr
open MathEvidence.Checkers.RationalEquality

/-!
Hand-written certificates that replay offline (no adapters).
-/

/-- `x + 0 = x` -/
def claim_add0 : Claim where
  varNames := ["x"]
  lhs := .add (.var 0) (.int 0)
  rhs := .var 0

def req_add0 : Request := Request.ofClaim claim_add0

def cert_add0 : Certificate where
  requestDigest := req_add0.requestDigest
  denomFactors := []

/-- `(x * y) / y = x` with condition `y`. -/
def claim_cancel : Claim where
  varNames := ["x", "y"]
  lhs := .div (.mul (.var 0) (.var 1)) (.var 1)
  rhs := .var 0

def req_cancel : Request := Request.ofClaim claim_cancel

def cert_cancel : Certificate where
  requestDigest := req_cancel.requestDigest
  denomFactors := [.var 1]

/-- `1/x - 1/x = 0` with condition `x`. -/
def claim_sub_self : Claim where
  varNames := ["x"]
  lhs := .sub (.div (.int 1) (.var 0)) (.div (.int 1) (.var 0))
  rhs := .int 0

def req_sub_self : Request := Request.ofClaim claim_sub_self

def cert_sub_self : Certificate where
  requestDigest := req_sub_self.requestDigest
  denomFactors := [.var 0]

/-- False identity `x = x + 1` must be rejected. -/
def claim_false : Claim where
  varNames := ["x"]
  lhs := .var 0
  rhs := .add (.var 0) (.int 1)

def req_false : Request := Request.ofClaim claim_false

def cert_false : Certificate where
  requestDigest := req_false.requestDigest
  denomFactors := []

/-- Digest mismatch must be rejected. -/
def cert_bad_digest : Certificate where
  requestDigest := ⟨"sha256:0000000000000000000000000000000000000000000000000000000000000000"⟩
  denomFactors := []

/-- Missing denominator coverage rejected. -/
def cert_cancel_missing : Certificate where
  requestDigest := req_cancel.requestDigest
  denomFactors := []

theorem replay_add0 :
    checkBool req_add0 cert_add0 = true := by native_decide

theorem replay_cancel :
    checkBool req_cancel cert_cancel = true := by native_decide

theorem replay_sub_self :
    checkBool req_sub_self cert_sub_self = true := by native_decide

theorem reject_false :
    checkBool req_false cert_false = false := by native_decide

theorem reject_bad_digest :
    checkBool req_add0 cert_bad_digest = false := by native_decide

theorem reject_missing_denom :
    checkBool req_cancel cert_cancel_missing = false := by native_decide

theorem replay_report_add0 :
    (replay { request := req_add0, certificate := cert_add0 }).accepted = true := by
  native_decide

/-- Soundness instantiation for the add0 certificate. -/
theorem sound_add0 :
    Claim.proposition claim_add0 cert_add0.denomFactors :=
  checkBool_sound req_add0 cert_add0 replay_add0

end MathEvidence.Checkers.RationalEquality.Tests
