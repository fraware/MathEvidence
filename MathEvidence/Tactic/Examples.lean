/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Tactic.Discovery
import MathEvidence.Tactic.Mathevidence

namespace MathEvidence.Tactic.Examples

open MathEvidence.Tactic
open MathEvidence.Tactic.Discovery
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Checkers.RationalEquality.OfflineFixtures

/-- Replay SymPy committed evidence offline (no backend process). -/
example : True := by
  mathevidence replay .basicSympy

/-- Replay Mathematica committed evidence offline (no backend process). -/
example : True := by
  mathevidence (mode := .replay) (operation := .rationalEquality)
    (backend := .mathematica) (claim := .soundResult)
    (bundle := .basicMathematica)

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

/-- Classic identity closes under an explicit nonzero denominator hypothesis.

Uses Meta reification + offline fixture match (no adapter spawn). -/
example (x : ℚ) (hx : x - 1 ≠ 0) :
    (x ^ 2 - 1) / (x - 1) = x + 1 := by
  mathevidence

end MathEvidence.Tactic.Examples
