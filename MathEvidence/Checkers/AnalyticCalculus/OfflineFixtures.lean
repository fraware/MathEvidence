/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.AnalyticCalculus.Check
import MathEvidence.Checkers.AnalyticCalculus.Soundness

/-!
# Offline analytic fixtures (ME-RV-054)

Hand-written replay fixtures for theorem-producing paths without a live backend.
-/

namespace MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures

open MathEvidence.IR.AnalyticExpr
open MathEvidence.Checkers.AnalyticCalculus

/-- Product rule offline fixture. -/
def cert_product : DerivCertificate where
  source := .mul (.variable 0) (.variable 0)
  derivative := .add (.mul (.const 1) (.variable 0)) (.mul (.variable 0) (.const 1))
  proof := .mul .variable .variable

theorem replay_product : checkDeriv cert_product = true := by native_decide

theorem sound_product (x : ℝ) :
    HasDerivAt cert_product.source.interpret
      (cert_product.derivative.interpret x) x :=
  checkDeriv_sound cert_product x replay_product (fun i => Fin.elim0 i)

/-- Log under positivity offline fixture. -/
def cert_log : DerivCertificate where
  source := .log (.variable 0)
  derivative := .div (.const 1) (.variable 0)
  proof := .log .variable 0
  obligations := #[.positive (.variable 0)]

theorem replay_log : checkDeriv cert_log = true := by native_decide

theorem sound_log (x : ℝ) (hx : 0 < x) :
    HasDerivAt cert_log.source.interpret (cert_log.derivative.interpret x) x :=
  checkDeriv_sound cert_log x replay_log (by
    intro i
    fin_cases i
    simpa [DomainObligation.holds, Expr.interpret] using hx)

/-- ODE `y = x^2`, `y' = 2x`, `y(0)=0`. -/
def cert_ode_sq : ODECertificate where
  solution := .pow (.variable 0) 2
  rhs := .mul (.mul (.const 2) (.pow (.variable 0) 1)) (.const 1)
  derivProof := .pow 2 .variable
  initialConditions := #[{ point := .const 0, value := .const 0 }]
  domain := Set.univ

theorem replay_ode_sq : checkODE cert_ode_sq = true := by native_decide

theorem sound_ode_sq :
    CandidateSolvesFirstOrderODE
      cert_ode_sq.solution.interpret cert_ode_sq.rhs.interpret
      cert_ode_sq.domain
      (cert_ode_sq.initialConditions.toList.map InitialCondition.asPair) :=
  checkODE_sound cert_ode_sq replay_ode_sq
    (fun _ _ i => Fin.elim0 i)
    (by
      intro ic hic
      have : ic = { point := .const 0, value := .const 0 } := by
        simp [cert_ode_sq] at hic
        exact hic
      subst this
      simp [Expr.interpret])

end MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures
