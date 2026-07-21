/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.Checkers.Counterexample.Tests
import MathEvidence.Tactic.Counterexample

/-!
# Ordinary finite-counterexample theorems via Meta reify + checker gate
-/

namespace MathEvidence.Tactic.Examples.Counterexample

/-- Ordinary `¬∀` over `Fin`. -/
theorem not_all_fin_val_zero : ¬ ∀ x : Fin 3, (x : Nat) = 0 := by
  mathevidence_counterexample

/-- Ordinary `¬∀` over `Bool`. -/
theorem not_all_bool_true : ¬ ∀ b : Bool, b = true := by
  mathevidence_counterexample

/-- Ordinary bounded-Nat Meta path (`∀ x : Nat, x ≤ n → x = k`). -/
theorem not_all_nat_le_three_eq_zero : ¬ ∀ x : Nat, x ≤ 3 → x = 0 := by
  mathevidence_counterexample

/-- Ordinary bounded-Int Meta path (`∀ x : Int, lo ≤ x → x ≤ hi → x = k`). -/
theorem not_all_int_bound_eq_one : ¬ ∀ x : Int, (0 : Int) ≤ x → x ≤ 2 → x = 1 := by
  mathevidence_counterexample

/-- Bounded Nat encoded via `Fin` (public Meta path; same IR family). -/
theorem not_all_nat_bound_via_fin : ¬ ∀ x : Fin 4, (x : Nat) = 0 := by
  mathevidence_counterexample

/-- End-to-end: operational search budget exhaust yields `unknown`, not a truth proof. -/
theorem search_budget_exhaust_is_unknown :
    MathEvidence.Checkers.Counterexample.searchCounterexample
        MathEvidence.Checkers.Counterexample.Tests.claim_nat_eq0 0 =
      .unknown "zero operational search budget" :=
  MathEvidence.Checkers.Counterexample.Tests.search_zero_budget_unknown

/-- Dependent-bound empty search also returns `unknown` (not completeness). -/
theorem search_empty_domain_is_unknown :
    MathEvidence.Checkers.Counterexample.searchCounterexample
        MathEvidence.Checkers.Counterexample.Tests.claim_empty_dependent_int 10 =
      .unknown "finite search found no refuting witness; this is not a truth proof" :=
  MathEvidence.Checkers.Counterexample.Tests.search_empty_domain_unknown

/-- Ordinary bounded-Nat refutation (hand proof; Meta IR path covers Fin encoding above). -/
theorem ordinary_bounded_nat_refutation :
    ¬ (∀ x : Nat, x ≤ 3 → x = 0) :=
  MathEvidence.Checkers.Counterexample.Tests.ordinary_nat_refutation

/-- Offline fixture soundness remains the IR proposition authority. -/
theorem offline_nat_eq0_proposition :
    MathEvidence.Checkers.Counterexample.Claim.proposition
      MathEvidence.Checkers.Counterexample.Tests.claim_nat_eq0
      MathEvidence.Checkers.Counterexample.Tests.cert_nat_eq0.witness :=
  MathEvidence.Checkers.Counterexample.Tests.sound_nat_eq0

end MathEvidence.Tactic.Examples.Counterexample
