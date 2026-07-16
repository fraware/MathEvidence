/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
import MathEvidence.Tactic.Basic
import MathEvidence.Tactic.Status
import MathEvidence.Tactic.ReifyRational
import MathEvidence.Tactic.Discovery
import MathEvidence.Tactic.Mathevidence
import MathEvidence.Tactic.Examples

/-!
# MathEvidence.Tactic

Lean elaborator and tactic UX (`mathevidence`).

- Discovery mode: Meta-reify ℚ equality; offline fixture match by default;
  live adapter spawn when `MATHEVIDENCE_DISCOVERY=1`.
- Replay mode: load a committed bundle, run `RationalEquality.check`, report §12.1 fields.
-/
