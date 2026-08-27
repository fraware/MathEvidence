/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.Replay
import MathEvidence.Checkers.RationalEquality.Soundness
import MathEvidence.Checkers.RationalEquality.SpecProp
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

def req_add0 : Request := Request.ofClaim! claim_add0

def cert_add0 : Certificate where
  requestDigest := req_add0.requestDigest
  denomFactors := []

/-- `(x * y) / y = x` with condition `y`. -/
def claim_cancel : Claim where
  varNames := ["x", "y"]
  lhs := .div (.mul (.var 0) (.var 1)) (.var 1)
  rhs := .var 0

def req_cancel : Request := Request.ofClaim! claim_cancel

def cert_cancel : Certificate where
  requestDigest := req_cancel.requestDigest
  denomFactors := [.var 1]

/-- `1/x - 1/x = 0` with condition `x`. -/
def claim_sub_self : Claim where
  varNames := ["x"]
  lhs := .sub (.div (.int 1) (.var 0)) (.div (.int 1) (.var 0))
  rhs := .int 0

def req_sub_self : Request := Request.ofClaim! claim_sub_self

def cert_sub_self : Certificate where
  requestDigest := req_sub_self.requestDigest
  denomFactors := [.var 0]

/-- Canonical rational literals are structural values, not domain assumptions. -/
def claim_half : Claim where
  varNames := []
  lhs := .add (.rat 1 2) (.int 0)
  rhs := .rat 1 2

def req_half : Request := Request.ofClaim! claim_half

def cert_half : Certificate where
  requestDigest := req_half.requestDigest
  denomFactors := []

/-- A zero literal denominator remains malformed through `wellFormed`. -/
def claim_zero_literal_denom : Claim where
  varNames := []
  lhs := .rat 1 0
  rhs := .int 0

def req_zero_literal_denom : Request := Request.ofClaim! claim_zero_literal_denom

def cert_zero_literal_denom : Certificate where
  requestDigest := req_zero_literal_denom.requestDigest
  denomFactors := []

/-- False identity `x = x + 1` must be rejected. -/
def claim_false : Claim where
  varNames := ["x"]
  lhs := .var 0
  rhs := .add (.var 0) (.int 1)

def req_false : Request := Request.ofClaim! claim_false

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

theorem replay_half_without_domain_factor :
    checkBool req_half cert_half = true := by native_decide

theorem reject_zero_literal_denom :
    checkBool req_zero_literal_denom cert_zero_literal_denom = false := by native_decide

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
    Claim.proposition req_add0.claim cert_add0.denomFactors :=
  checkBool_sound req_add0 cert_add0 replay_add0

/-- Literal definedness is discharged by well-formedness in the soundness proof. -/
theorem sound_half_without_domain_factor :
    Claim.proposition req_half.claim cert_half.denomFactors :=
  checkBool_sound req_half cert_half replay_half_without_domain_factor

end MathEvidence.Checkers.RationalEquality.Tests
