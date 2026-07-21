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

/-- Redundant extra condition (well-formed under a single variable). -/
def cond_redundant : Expr := Expr.add (Expr.var 0) (Expr.int 0)

/-- Ill-formed-index helper retained for deletion unit test (never in sufficiency set). -/
def cond_y : Expr := Expr.var 1

theorem sufficient_minimal :
    isSufficient req_basic [cond_x_minus_1] = true := by native_decide

theorem insufficient_empty :
    isSufficient req_basic ([] : List Expr) = false := by native_decide

/-- Boolean projection of typed proveSufficient for `native_decide` tests. -/
def proveSufficientProvedOk
    (req : MathEvidence.Checkers.RationalEquality.Request) (conds : List Expr) : Bool :=
  match proveSufficient req conds with
  | .proved e =>
      e.theoremDecl == "MathEvidence.Hypothesis.sufficient_implies_proposition" &&
        e.checkerDecl == "MathEvidence.Checkers.RationalEquality.checkBool" &&
        e.detail == "checkBool_accept"
  | _ => false

def proveSufficientFailedDetail
    (req : MathEvidence.Checkers.RationalEquality.Request) (conds : List Expr) : String :=
  match proveSufficient req conds with
  | .failed e => e.detail
  | .proved e => e.detail
  | .unknown e => e.detail

/-- `proveSufficient` returns typed `proved` with theorem/checker decl citations. -/
theorem prove_sufficient_proved_shape :
    proveSufficientProvedOk req_basic [cond_x_minus_1] = true := by
  native_decide

/-- Empty conditions fail with an explicit coverage reject detail. -/
theorem prove_sufficient_failed_empty :
    proveSufficientFailedDetail req_basic ([] : List Expr) =
      "denom_coverage_incomplete" := by
  native_decide

/-- Denom coverage alone is not sufficiency: false identity with covered denoms. -/
theorem denom_coverage_alone_not_sufficient :
    let req := MathEvidence.Checkers.RationalEquality.OfflineFixtures.req_false_identity
    let conds := [Expr.var 0]
    denomCoverageOnly req conds = true ∧
      polyIdentityOnly req = false ∧
      isSufficient req conds = false ∧
      proveSufficientFailedDetail req conds = "poly_identity_failed" := by
  native_decide

theorem delete_redundant_extra :
    deleteHypothesis req_basic [cond_x_minus_1, cond_redundant] cond_redundant =
      .redundant [cond_x_minus_1] := by native_decide

/-- Deletion of an unused factor that is not in the set is missing; when present only
as the deleted target after a well-formed prefix, remaining stays sufficient. -/
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

/-- End-to-end Product 03: sufficiency → deletion → certified CEX on weaker variant. -/
def e2eLattice : ConditionLattice :=
  buildConditionLatticeWithCex "e2e_lattice" req_basic
    [{ id := "extra", expr := cond_redundant }]
    [{ id := "c0", expr := cond_x_minus_1 }]
    MathEvidence.Checkers.Counterexample.Tests.req_nat_eq0
    MathEvidence.Checkers.Counterexample.Tests.cert_nat_eq0
    "cex_nat_eq0"
    ["c0"]

theorem e2e_claims_not_minimal :
    e2eLattice.claimsMinimal = false := by native_decide

theorem e2e_has_sufficient_set :
    e2eLattice.sufficientSets = [["extra", "c0"]] := by native_decide

theorem e2e_deletes_redundant_extra :
    e2eLattice.redundant = ["extra"] := by native_decide

theorem e2e_certified_cex :
    e2eLattice.certifiedCounterexamples = ["cex_nat_eq0"] := by native_decide

end MathEvidence.Hypothesis.Tests
