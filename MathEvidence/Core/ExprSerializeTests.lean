/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.Core.EnvironmentLock
import MathEvidence.Core.ExprSerialize
import MathEvidence.Core.TheoremIdentity

/-!
# ME-RV-020 Expr serialize tests

Compile-time Meta checks that digests use kernel Expr walks (not `ppExpr`),
that binders participate, and that distinct binder shapes yield distinct digests.
-/

namespace MathEvidence.Core.ExprSerializeTests

open Lean Meta Elab Term
open MathEvidence.Core
open MathEvidence.Core.ExprSerialize

private def hasSubstr (haystack needle : String) : Bool :=
  (haystack.splitOn needle).length > 1

private def envLockDig : MetaM ContentDigest := do
  match EnvironmentLock.rationalEqualityDefault.digest with
  | .ok d => pure d
  | .error e => throwError s!"env lock digest failed: {e}"

/-- `#test_theorem_identity_expr` — Meta-side ME-RV-020 vectors. -/
elab "#test_theorem_identity_expr" : command => do
  Command.liftTermElabM do
    let lock ← envLockDig
    let ty ← elabTerm (← `(∀ x : Nat, x = x)) none
    let ty ← instantiateMVars ty
    let id1 ← theoremTypeIdentityOfExpr ty lock
    let ser := id1.elaboratedSerialization
    unless (ser.startsWith "(forall" || hasSubstr ser "(const") do
      throwError "expected kernel Expr serialization, got: {ser}"
    unless id1.binders.length ≥ 1 do
      throwError "expected at least one binder from telescope"
    unless id1.constantNames.any (fun s => s == "Eq" || s.endsWith ".Eq") do
      throwError s!"expected Eq in constantNames, got {id1.constantNames}"
    let d1 ←
      match id1.digest with
      | .ok d => pure d
      | .error e => throwError e
    let pretty ← toString <$> ppExpr ty
    unless id1.elaboratedSerialization ≠ pretty do
      throwError "structural Expr serialization collided with ppExpr (unexpected)"
    let ty2 ← elabTerm (← `(∀ {x : Nat}, x = x)) none
    let ty2 ← instantiateMVars ty2
    let id2 ← theoremTypeIdentityOfExpr ty2 lock
    let d2 ←
      match id2.digest with
      | .ok d => pure d
      | .error e => throwError e
    unless d1.value ≠ d2.value do
      throwError "expected distinct digests for default vs implicit Nat binders"
    -- Proof-term path: structural serializeExpr, never Expr.hash.
    let proofSer ← proofTermSerializationOfConst? ``Nat.add_zero
    match proofSer with
    | none =>
      throwError "expected proof term serialization for Nat.add_zero"
    | some ps =>
      unless (ps.startsWith "(lam" || ps.startsWith "(app" || hasSubstr ps "(const") do
        throwError "expected kernel proof-term serialization, got: {ps}"
      unless !(hasSubstr ps "Expr.hash") do
        throwError "proof-term serialization must not mention Expr.hash"
    let proofDig ← proofTermDigestOfConst? ``Nat.add_zero lock
    match proofDig with
    | none => throwError "expected proof-term digest for Nat.add_zero"
    | some pd =>
      unless pd.value.startsWith "sha256:" do
        throwError s!"expected sha256 proof-term digest, got {pd.value}"
    logInfo m!"ME-RV-020 ExprSerialize tests ok digests={d1.value} / {d2.value}"

#test_theorem_identity_expr

end MathEvidence.Core.ExprSerializeTests
