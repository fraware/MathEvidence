/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.AnalyticCalculus.Spec
import MathEvidence.Checkers.AnalyticCalculus.Certificate
import MathEvidence.Checkers.AnalyticCalculus.Check
import MathEvidence.Checkers.AnalyticCalculus.Soundness
import MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures
import MathEvidence.Checkers.AnalyticCalculus.ReplaySound
import MathEvidence.Checkers.AnalyticCalculus.Tests

/-!
# Analytic calculus barrel (ME-RV-050..054)

Split implementation lives in Spec / Certificate / Check / Soundness / Tests.
Importing this module pulls the public checker surface formerly in a monolith
`Basic.lean`.
-/
