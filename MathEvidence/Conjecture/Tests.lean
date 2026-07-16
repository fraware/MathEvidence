/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Conjecture.Engine
import MathEvidence.Checkers.Counterexample.Tests

namespace MathEvidence.Conjecture.Tests

open MathEvidence.IR.FinitePredicate
open MathEvidence.Conjecture

/-- Small nat family for Product 04 demos. -/
def nat3Family : FinitePredicateFamily where
  id := "finite.nat_le_3"
  varNames := ["x"]
  domains := [{ ty := .nat, bound := some 3 }]
  enumerateBound := 4

def pred_eq0 : Pred := .eq (.var 0) (.lit (.nat 0))

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

end MathEvidence.Conjecture.Tests
