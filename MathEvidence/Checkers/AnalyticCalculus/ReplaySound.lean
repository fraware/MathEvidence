/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.AnalyticCalculus.Soundness
import MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures

/-!
# Analytic OfflineFixtures packaging (not exact CR authority)

`replaySound` / fixture `certified_analytic_replay_product` package OfflineFixtures
for protocol self-tests. Exact-candidate Certification Records bind
`checkDeriv_sound` / `checkDerivWithin_sound` / `checkAntideriv_sound` /
`checkODE_sound` from `Soundness.lean` via the typed exact generator — never by
substituting these fixtures for a different submitted candidate.
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
