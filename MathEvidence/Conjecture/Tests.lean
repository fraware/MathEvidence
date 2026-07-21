/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Conjecture.Engine
import MathEvidence.Conjecture.Precision
import MathEvidence.Conjecture.Domains.FiniteGraph
import MathEvidence.Checkers.Counterexample.Tests

namespace MathEvidence.Conjecture.Tests

open MathEvidence.IR.FinitePredicate
open MathEvidence.Conjecture

/-- Small nat family for Product 04 **regression fixtures** (not the primary
vertical — see `Domains.FiniteGraph`). -/
def nat3Family : FinitePredicateFamily where
  id := "finite.nat_le_3"
  varNames := ["x"]
  domains := [{ ty := .nat, bound := some 3 }]
  enumerateBound := 4

def pred_eq0 : Pred := .eq (.var 0) (.lit (.nat 0))

/-- Reflexive equality — formally provable on the family. -/
def pred_eq_refl : Pred := .eq (.var 0) (.var 0)

/-- Bounded survivor used as an explicit open-problem lift target. -/
def pred_le_self : Pred := .le (.var 0) (.var 0)

def ep0 : Episode := observePattern nat3Family.id pred_eq0

def ep1 : Episode := toCandidate ep0

theorem candidate_not_theorem :
    ep1.state.isTheoremGrade = false := by native_decide

/-- Align with Counterexample.Tests fixture (same claim shape). -/
def req_eq0_fixture := MathEvidence.Checkers.Counterexample.Tests.req_nat_eq0
def cert_eq0_fixture := MathEvidence.Checkers.Counterexample.Tests.cert_nat_eq0

theorem falsify_eq0 :
    (certifyRefutation ep1 req_eq0_fixture cert_eq0_fixture
      "cex_nat_eq0").state = .falsified := by native_decide

theorem bounded_not_theorem :
    let e := markBoundedVerified ep1 4
    e.state = .boundedVerified ∧ e.state.isTheoremGrade = false := by native_decide

theorem campaign_survivors_exclude_falsified :
    let C0 : Campaign := { family := nat3Family }
    let eF := certifyRefutation ep1 req_eq0_fixture cert_eq0_fixture "cex"
    let C := C0.addEpisode eF
    C.survivors = ([] : List Episode) := by native_decide

/-- Formal family campaign: falsify false candidate; prove reflexive survivor;
leave an explicit open-problem artifact for a non-trivial survivor. -/
def campaignDemo : Campaign :=
  let C0 : Campaign := { family := nat3Family }
  let eFalse :=
    certifyRefutation (toCandidate (observePattern nat3Family.id pred_eq0))
      req_eq0_fixture cert_eq0_fixture "cex_nat_eq0"
  let eThm :=
    markFormallyProved
      (toCandidate (observePattern nat3Family.id pred_eq_refl))
      "MathEvidence.Conjecture.Tests.eq_refl_on_nat3"
  let eOpen :=
    markOpenProblem
      (markBoundedVerified
        (toCandidate (observePattern nat3Family.id pred_le_self)) 4)
      "OPEN: lift ∀ x ≤ 3, x ≤ x to unbounded ℕ without finite-domain restriction (see open-problem artifact)."
  C0.addEpisode eFalse |>.addEpisode eThm |>.addEpisode eOpen

/-- Reusable theorem for the surviving reflexive candidate. -/
theorem eq_refl_on_nat3 (x : Nat) (_hx : x ≤ 3) : x = x := rfl

theorem campaign_precision_accounting :
    let A := campaignDemo.precisionAccounting
    A.proposed = 3 ∧ A.falsified = 1 ∧ A.formallyProved = 1 ∧ A.openProblems = 1 ∧
      A.formallyProved + A.openProblems = 2 := by
  native_decide

theorem campaign_has_open_and_theorem :
    (campaignDemo.episodes.map (·.state)).contains .formallyProved = true ∧
      (campaignDemo.episodes.map (·.state)).contains .open_ = true := by
  native_decide

/-- Primary vertical smoke: graph plugin falsification is reachable from Tests. -/
theorem finite_graph_plugin_falsifies :
    MathEvidence.Conjecture.Domains.FiniteGraph.campaignDemo.precisionAccounting.falsified = 1 := by
  native_decide

end MathEvidence.Conjecture.Tests
