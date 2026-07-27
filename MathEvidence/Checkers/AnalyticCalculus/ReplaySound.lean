/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.AnalyticCalculus.Soundness
import MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures

/-!
# Analytic kernel-replay soundness (ME-RV-054)

`replaySound` / fixture `certified_analytic_replay_product` are the
theorem-producing authority for analytic derivative kernel replay, parallel to
Wave 2 rational `replaySound`.
-/

namespace MathEvidence.Checkers.AnalyticCalculus

open MathEvidence.IR.AnalyticExpr
open MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures

/-- Kernel-replay soundness package: checker acceptance + domain hypotheses
imply `HasDerivAt` on the interpreted source. -/
theorem replaySound (c : DerivCertificate) (x : ℝ)
    (hCheck : checkDeriv c = true)
    (hDom : SatisfiesObligations c.obligations x) :
    HasDerivAt c.source.interpret (c.derivative.interpret x) x :=
  checkDeriv_sound c x hCheck hDom

/-- Compiled positive fixture: product rule offline certificate. -/
theorem certified_analytic_replay_product (x : ℝ) :
    HasDerivAt cert_product.source.interpret
      (cert_product.derivative.interpret x) x :=
  replaySound cert_product x replay_product (fun i => Fin.elim0 i)

#print axioms certified_analytic_replay_product

end MathEvidence.Checkers.AnalyticCalculus
