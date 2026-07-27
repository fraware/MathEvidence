/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Bridge
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.IR.RationalExpr.Reify
import MathEvidence.Tactic.Discovery
import MathEvidence.Tactic.Mathevidence
import MathEvidence.Tactic.ReifyRational

namespace MathEvidence.Tactic.Examples

open MathEvidence.Tactic
open MathEvidence.Tactic.Discovery
open MathEvidence.Tactic.ReifyRational
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Checkers.RationalEquality.OfflineFixtures
open MathEvidence.IR.RationalExpr

/-- Shared checker rejects false identities from either backend path. -/
theorem false_identity_rejected :
    checkBool req_false_identity cert_false_identity = false :=
  reject_false_identity

/-- Shared checker rejects request digest mismatches. -/
theorem hash_mismatch_rejected :
    checkBool req_hash_mismatch cert_hash_mismatch = false :=
  reject_hash_mismatch

/-- Lean JCS binding for the classic claim matches the committed wire digest. -/
theorem lean_wire_digest_matches_basic_sympy :
    (match bindRequestDigest claim_basic_sympy with
     | .ok (_, d) => d == digest_basic_sympy
     | .error _ => false) = true := by
  native_decide

/-- Offline discovery matches the classic SymPy fixture by IR equality. -/
theorem offline_match_basic_sympy :
    matchOfflineBundle claim_basic_sympy = some .basicSympy := by
  native_decide

/-- Prefer Mathematica offline fixture when discovery backend is Mathematica. -/
theorem offline_match_basic_mathematica :
    matchOfflineBundle claim_basic_mathematica .mathematica = some .basicMathematica := by
  native_decide

/-- Classic identity closes under an explicit nonzero denominator hypothesis.

Uses Meta reification + offline fixture match (no adapter spawn).
After checker accept, closes via `sound_*` / `eq_of_proposition` (ME-RV-023);
`hx` discharges Bridge side conditions — not an independent `field_simp; ring`.
Status report lists claim requested/established, bundle path, remaining goals. -/
example (x : ℚ) (hx : x - 1 ≠ 0) :
    (x ^ 2 - 1) / (x - 1) = x + 1 := by
  mathevidence

/-- Theorem-producing offline replay of the committed SymPy bundle. -/
example (x : ℚ) (hx : x - 1 ≠ 0) :
    (x ^ 2 - 1) / (x - 1) = x + 1 := by
  mathevidence replay .basicSympy

/-- Same identity with Mathematica offline fixture (explicit backend). -/
example (x : ℚ) (hx : x - 1 ≠ 0) :
    (x ^ 2 - 1) / (x - 1) = x + 1 := by
  mathevidence discovery with .mathematica

/-- Non-fixture live Bridge close (ME-RV-023 / E-12): not a protocol-reference
fixture; authority is elaborated `eq_of_replaySound`, not `field_simp; ring`. -/
example (x : ℚ) : x + 0 = x :=
  close_live_add0 x

/-- Non-fixture cancel identity; denom hyp discharges Bridge side conditions. -/
example (x y : ℚ) (hy : y ≠ 0) : (x * y) / y = x :=
  close_live_cancel x y hy

/-- Adversarial: wrong digest is rejected before Bridge. -/
theorem adversarial_wrong_digest_rejected :
    checkBool req_live_add0
      { requestDigest :=
          ⟨"sha256:0000000000000000000000000000000000000000000000000000000000000000"⟩
        denomFactors := [] } = false :=
  adversarial_live_wrong_digest_rejected

/-- Adversarial: missing denom coverage is rejected before Bridge. -/
theorem adversarial_missing_denom_rejected :
    checkBool req_live_cancel
      { requestDigest := req_live_cancel.requestDigest, denomFactors := [] } = false :=
  adversarial_live_missing_denom_rejected

/-- Adversarial: unsupported syntax is rejected at reification (never Bridge-closed). -/
theorem adversarial_unsupported_syntax_rejected :
    Reject.format (.unsupportedExpression "Real.sin") =
      "unsupportedExpression: Real.sin" :=
  rfl

/- Inspect SymPy committed evidence offline (no backend process, no goal close). -/
#mathevidence inspect .basicSympy

/- Inspect Mathematica committed evidence offline (no backend process, no goal close). -/
#mathevidence inspect .basicMathematica

/- Linear-algebra inverse witness offline inspection (R4). -/
#mathevidence inspect .laInverse2x2

/- Finite counterexample offline inspection (R4). -/
#mathevidence inspect .cexSimpleFalseUniversal

/- Intentional reject fixtures still report status but never close goals. -/
#mathevidence inspect .laSingularInverseRejected

#mathevidence inspect .cexOutOfDomainRejected

end MathEvidence.Tactic.Examples
