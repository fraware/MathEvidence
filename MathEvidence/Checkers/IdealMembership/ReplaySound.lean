/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.IdealMembership.Soundness
import MathEvidence.Checkers.IdealMembership.Spec

/-!
# Ideal-membership kernel-replay soundness (ME-RV-035 / P0-F)

`replaySound` is the theorem-producing authority for ideal-membership kernel
replay. Proof uses `checkBool_sound` — not an independent final `ring` on the
original Mathlib goal.
-/

namespace MathEvidence.Checkers.IdealMembership

/-- Kernel-replay soundness: checker acceptance implies the claim proposition. -/
theorem replaySound {m : Nat}
    (req : Request m)
    (cert : Certificate m)
    (hCheck : checkBool req cert = true) :
    Claim.proposition req.claim :=
  checkBool_sound req cert hCheck

end MathEvidence.Checkers.IdealMembership
