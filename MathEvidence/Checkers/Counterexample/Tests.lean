/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.Checkers.Counterexample.Replay
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.IR.FinitePredicate.Syntax

namespace MathEvidence.Checkers.Counterexample.Tests

open MathEvidence.IR.FinitePredicate
open MathEvidence.Checkers.Counterexample

/-!
Hand-written offline fixtures: typed witnesses that falsify finite predicates.
-/

/-- Predicate `x = 0` over `nat ≤ 3`; witness `x = 2` is a counterexample. -/
def claim_nat_eq0 : Claim where
  varNames := ["x"]
  domains := [{ ty := .nat, bound := some 3 }]
  pred := .eq (.var 0) (.lit (.nat 0))
  claimClass := .refutation

def req_nat_eq0 : Request := Request.ofClaim claim_nat_eq0

def cert_nat_eq0 : Certificate where
  requestDigest := req_nat_eq0.requestDigest
  witness := [.nat 2]

/-- Predicate `b = true`; witness `false` refutes it. -/
def claim_bool : Claim where
  varNames := ["b"]
  domains := [{ ty := .bool }]
  pred := .eq (.var 0) (.lit (.bool true))
  claimClass := .refutation

def req_bool : Request := Request.ofClaim claim_bool

def cert_bool : Certificate where
  requestDigest := req_bool.requestDigest
  witness := [.bool false]

/-- Predicate `x + y = 5` over small ints; witness `(1,1)` refutes. -/
def claim_sum : Claim where
  varNames := ["x", "y"]
  domains :=
    [{ ty := .int, bound := some 5 }, { ty := .int, bound := some 5 }]
  pred := .eq (.add (.var 0) (.var 1)) (.lit (.int 5))
  claimClass := .refutation

def req_sum : Request := Request.ofClaim claim_sum

def cert_sum : Certificate where
  requestDigest := req_sum.requestDigest
  witness := [.int 1, .int 1]

/-- Dependent Nat bound: `0 ≤ y ≤ x`, with witness `(x,y) = (2,1)`. -/
def claim_dependent_nat : Claim where
  varNames := ["x", "y"]
  domains :=
    [ { ty := .nat, bound := some 3 },
      { ty := .nat, upperBound := some (.var 0) } ]
  pred := .eq (.var 1) (.var 0)
  claimClass := .refutation

def req_dependent_nat : Request := Request.ofClaim claim_dependent_nat

def cert_dependent_nat : Certificate where
  requestDigest := req_dependent_nat.requestDigest
  witness := [.nat 2, .nat 1]

/-- Dependent-bound violation: `y = 3` is outside `0 ≤ y ≤ x` when `x = 2`. -/
def cert_dependent_nat_ood : Certificate where
  requestDigest := req_dependent_nat.requestDigest
  witness := [.nat 2, .nat 3]

/-- Empty dependent Int interval: lower bound `1`, upper bound `0`. -/
def claim_empty_dependent_int : Claim where
  varNames := ["x"]
  domains :=
    [{ ty := .int, lowerBound := some (.lit (.int 1)), upperBound := some (.lit (.int 0)) }]
  pred := .eq (.var 0) (.lit (.int 0))
  claimClass := .refutation

def req_empty_dependent_int : Request := Request.ofClaim claim_empty_dependent_int

def cert_empty_dependent_int : Certificate where
  requestDigest := req_empty_dependent_int.requestDigest
  witness := [.int 0]

/-- Witness that makes the predicate true must be rejected. -/
def cert_nat_eq0_true : Certificate where
  requestDigest := req_nat_eq0.requestDigest
  witness := [.nat 0]

/-- Out-of-domain witness rejected. -/
def cert_nat_ood : Certificate where
  requestDigest := req_nat_eq0.requestDigest
  witness := [.nat 9]

/-- Type mismatch: bool witness for nat domain rejected. -/
def cert_type_mismatch : Certificate where
  requestDigest := req_nat_eq0.requestDigest
  witness := [.bool false]

/-- Digest mismatch rejected. -/
def cert_bad_digest : Certificate where
  requestDigest := ⟨"sha256:0000000000000000000000000000000000000000000000000000000000000000"⟩
  witness := [.nat 2]

theorem replay_nat_eq0 :
    checkBool req_nat_eq0 cert_nat_eq0 = true := by native_decide

theorem replay_bool :
    checkBool req_bool cert_bool = true := by native_decide

theorem replay_sum :
    checkBool req_sum cert_sum = true := by native_decide

theorem replay_dependent_nat :
    checkBool req_dependent_nat cert_dependent_nat = true := by native_decide

theorem reject_true_witness :
    checkBool req_nat_eq0 cert_nat_eq0_true = false := by native_decide

theorem reject_ood :
    checkBool req_nat_eq0 cert_nat_ood = false := by native_decide

theorem reject_dependent_ood :
    checkBool req_dependent_nat cert_dependent_nat_ood = false := by native_decide

theorem reject_empty_dependent_domain_witness :
    checkBool req_empty_dependent_int cert_empty_dependent_int = false := by native_decide

theorem reject_type_mismatch :
    checkBool req_nat_eq0 cert_type_mismatch = false := by native_decide

theorem reject_bad_digest :
    checkBool req_nat_eq0 cert_bad_digest = false := by native_decide

theorem replay_report_bool :
    (replay { request := req_bool, certificate := cert_bool }).accepted = true := by
  native_decide

theorem sound_nat_eq0 :
    Claim.proposition claim_nat_eq0 cert_nat_eq0.witness :=
  checkBool_sound req_nat_eq0 cert_nat_eq0 replay_nat_eq0

theorem refutes_nat_eq0 :
    eval cert_nat_eq0.witness claim_nat_eq0.pred = some false :=
  checkBool_refutes req_nat_eq0 cert_nat_eq0 replay_nat_eq0

theorem search_zero_budget_unknown :
    searchCounterexample claim_nat_eq0 0 =
      .unknown "zero operational search budget" := by native_decide

theorem search_empty_domain_unknown :
    searchCounterexample claim_empty_dependent_int 10 =
      .unknown "finite search found no refuting witness; this is not a truth proof" := by
  native_decide

theorem search_dependent_finds_witness :
    searchCounterexample claim_dependent_nat 20 = .found [.nat 1, .nat 0] := by
  native_decide

/-- Ordinary Lean theorem: a concrete witness refutes the bounded universal. -/
theorem ordinary_nat_refutation :
    ¬ (∀ x : Nat, x ≤ 3 → x = 0) := by
  intro h
  have h2 : (2 : Nat) = 0 := h 2 (by decide)
  exact (Nat.succ_ne_zero 1) h2

end MathEvidence.Checkers.Counterexample.Tests
