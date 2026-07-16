/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Hypothesis.Build
import MathEvidence.Hypothesis.CounterexampleBridge
import MathEvidence.Checkers.Counterexample.Tests
import MathEvidence.Checkers.RationalEquality.OfflineFixtures

namespace MathEvidence.Hypothesis.Tests

open MathEvidence.IR.RationalExpr
open MathEvidence.Hypothesis

/-!
Hypothesis Synthesis fixtures over rational equality + finite counterexample.
-/

/-- Classic identity: `(x²-1)/(x-1) = x+1` needs `x-1 ≠ 0`. -/
def req_basic := MathEvidence.Checkers.RationalEquality.OfflineFixtures.req_basic_sympy

def cond_x_minus_1 : Expr := Expr.sub (Expr.var 0) (Expr.int 1)

/-- Redundant extra condition `y` (unused in the identity). -/
def cond_y : Expr := Expr.var 1

theorem sufficient_minimal :
    isSufficient req_basic [cond_x_minus_1] = true := by native_decide

theorem insufficient_empty :
    isSufficient req_basic ([] : List Expr) = false := by native_decide

theorem delete_redundant_y :
    deleteHypothesis req_basic [cond_x_minus_1, cond_y] cond_y =
      .redundant [cond_x_minus_1] := by native_decide

theorem delete_necessary_fails :
    deleteHypothesis req_basic [cond_x_minus_1] cond_x_minus_1 =
      .notRedundant ([] : List Expr) := by native_decide

theorem lattice_never_claims_minimal_by_default :
    let L := buildConditionLattice "test_lattice" req_basic
      [] [{ id := "c0", expr := cond_x_minus_1 }]
    L.claimsMinimal = false ∧ L.minimalitySound = true := by native_decide

/-- Weaker false universal `x = 0` on `nat ≤ 3` — certified via Counterexample. -/
theorem weaker_variant_certified :
    verifyCounterexample
      MathEvidence.Checkers.Counterexample.Tests.req_nat_eq0
      MathEvidence.Checkers.Counterexample.Tests.cert_nat_eq0 = .certified := by
  native_decide

theorem weaker_variant_sound :
    MathEvidence.Checkers.Counterexample.Claim.proposition
      MathEvidence.Checkers.Counterexample.Tests.claim_nat_eq0
      MathEvidence.Checkers.Counterexample.Tests.cert_nat_eq0.witness :=
  verifyCounterexample_sound
    MathEvidence.Checkers.Counterexample.Tests.req_nat_eq0
    MathEvidence.Checkers.Counterexample.Tests.cert_nat_eq0
    (by native_decide : MathEvidence.Checkers.Counterexample.checkBool
      MathEvidence.Checkers.Counterexample.Tests.req_nat_eq0
      MathEvidence.Checkers.Counterexample.Tests.cert_nat_eq0 = true)

theorem lattice_records_cex :
    let L0 := ConditionLattice.empty "cex_demo"
    let L := L0.recordCertifiedCounterexample "cex_nat_eq0" ["c0"] []
    L.certifiedCounterexamples = ["cex_nat_eq0"] ∧
      L.necessityProofs.head?.map (·.kind) = some .certifiedCounterexample := by
  native_decide

end MathEvidence.Hypothesis.Tests
