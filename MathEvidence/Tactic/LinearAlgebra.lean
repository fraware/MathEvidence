/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Rat.Defs
import MathEvidence.Checkers.LinearAlgebra.Bridge
import MathEvidence.Checkers.LinearAlgebra.Check
import MathEvidence.Checkers.LinearAlgebra.ReplaySound
import MathEvidence.Checkers.LinearAlgebra.Soundness
import MathEvidence.Encoding.Matrix
import MathEvidence.IR.MatrixExpr.Ops
import MathEvidence.Tactic.ReifyMatrix

/-!
# Linear-algebra tactic (ME-RV-040)

`mathevidence_linear_algebra` reifies concrete `Matrix (Fin m) (Fin n) ℚ`
goals into the exact matrix IR, gates on the Lean checker / IR predicates,
and closes **only** by applying Bridge / `replaySound` / `checkBool_sound`
transport theorems.

Supported shapes:

* `A * B = 1` / two-sided inverse (`isInverseWitness` / `isRightInverse`)
* `A.mulVec x = b` (`isSystemSolution`)
* `A.mulVec v = 0 ∧ v ≠ 0` (`isKernelVector`)
* `A.det = q` (`isDetIdentity`)

Independent `native_decide` is **not** the final theorem authority. It may
appear only inside Bridge lemmas to discharge decidable IR Boolean / densify
normalization obligations after soundness hypotheses are in scope.
-/

namespace MathEvidence.Tactic.LinearAlgebra

open Lean Meta Elab Tactic
open MathEvidence.IR.MatrixExpr
open MathEvidence.Tactic.ReifyMatrix
open MathEvidence.Checkers.LinearAlgebra

def unsupportedMessage : String :=
  "mathevidence linear algebra: unsupported goal. Supported shapes: concrete " ++
  "Matrix (Fin m) (Fin n) Rat products `A * B = 1` (and `A * B = 1 ∧ B * A = 1`), " ++
  "`A.mulVec x = b`, `A.mulVec v = 0 ∧ v ≠ 0`, and `A.det = q`. " ++
  "Symbolic matrices are rejected; offline fixtures remain via `#mathevidence inspect`."

private def isOneMatrix (e : Expr) : MetaM Bool := do
  let e ← whnfR e
  pure (e.isAppOf ``OfNat.ofNat || e.isAppOf ``One.one ||
    (match e.getAppFn.constName? with
     | some n => n.getString! == "one"
     | none => false))

private def isZeroVec (e : Expr) : MetaM Bool := do
  let e ← whnfR e
  pure (e.isAppOf ``OfNat.ofNat || e.isAppOf ``Zero.zero ||
    (match e.getAppFn.constName? with
     | some n => n.getString! == "zero"
     | none => false))

private def peelAnd? (e : Expr) : MetaM (Option (Expr × Expr)) := do
  let e ← whnf e
  if e.isAppOf ``And then
    let args := e.getAppArgs
    if args.size ≥ 2 then return some (args[args.size - 2]!, args[args.size - 1]!)
  return none

private def matchMulEqOne (e : Expr) : MetaM (Option (Expr × Expr)) := do
  let e ← whnf e
  unless e.isAppOf ``Eq do return none
  let args := e.getAppArgs
  if args.size < 3 then return none
  let lhs ← whnfR args[args.size - 2]!
  let rhs ← whnfR args[args.size - 1]!
  unless ← isOneMatrix rhs do return none
  if lhs.isAppOf ``HMul.hMul || lhs.isAppOf ``Mul.mul then
    let margs := lhs.getAppArgs
    if margs.size ≥ 2 then
      return some (margs[margs.size - 2]!, margs[margs.size - 1]!)
  return none

/-- Match `A.mulVec x = b` / `Matrix.mulVec A x = b`. -/
private def matchMulVecEq (e : Expr) : MetaM (Option (Expr × Expr × Expr)) := do
  let e ← whnf e
  unless e.isAppOf ``Eq do return none
  let args := e.getAppArgs
  if args.size < 3 then return none
  let lhs := args[args.size - 2]!
  let rhs ← whnfR args[args.size - 1]!
  let fn := lhs.getAppFn
  let name? := fn.constName?
  let isMulVec :=
    match name? with
    | some n =>
      let s := n.getString!
      s == "mulVec" || s.endsWith "mulVec"
    | none => false
  if isMulVec then
    let margs := lhs.getAppArgs
    if margs.size ≥ 2 then
      return some (margs[margs.size - 2]!, margs[margs.size - 1]!, rhs)
  return none

/-- Match `v ≠ 0` / `¬ v = 0`. -/
private def matchNeZeroVec (e : Expr) : MetaM (Option Expr) := do
  let e ← whnf e
  if e.isAppOf ``Ne then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      let rhs ← whnfR args[args.size - 1]!
      if ← isZeroVec rhs then
        return some args[args.size - 2]!
  if e.isAppOf ``Not then
    let inner ← whnf e.appArg!
    if inner.isAppOf ``Eq then
      let args := inner.getAppArgs
      if args.size ≥ 3 then
        let rhs ← whnfR args[args.size - 1]!
        if ← isZeroVec rhs then
          return some args[args.size - 2]!
  return none

private def matchDetEq (e : Expr) : MetaM (Option (Expr × Expr)) := do
  let e ← whnf e
  unless e.isAppOf ``Eq do return none
  let args := e.getAppArgs
  if args.size < 3 then return none
  let lhs := args[args.size - 2]!
  let rhs ← whnfR args[args.size - 1]!
  let fn := lhs.getAppFn
  let isDet :=
    match fn.constName? with
    | some n =>
      let s := n.getString!
      s == "det" || s.endsWith "det"
    | none => false
  if isDet then
    let margs := lhs.getAppArgs
    if margs.size ≥ 1 then
      return some (margs.back!, rhs)
  return none

/-- Close via Bridge soundness (IR Bool discharged by `native_decide` only).

Matrix/vector arguments unify from the goal; `eqProofs` are retained for
Certification Record / interpretation-proof emission (ME-RV-040). -/
private def closeRightInverse (_eqProofs : Array Expr) : TacticM Unit := do
  let _ := _eqProofs
  evalTactic (← `(tactic|
    refine MathEvidence.Checkers.LinearAlgebra.Bridge.right_inverse_of_isRightInverse
      _ _ (by native_decide)))

private def closeTwoSidedInverse (_eqProofs : Array Expr) : TacticM Unit := do
  let _ := _eqProofs
  evalTactic (← `(tactic|
    refine MathEvidence.Checkers.LinearAlgebra.Bridge.inverse_of_isInverseWitness
      _ _ (by native_decide)))

private def closeSystem (_eqProofs : Array Expr) : TacticM Unit := do
  let _ := _eqProofs
  -- General rectangular `system_of_isSystemSolution` (any Fin m × Fin n).
  try
    evalTactic (← `(tactic|
      refine MathEvidence.Checkers.LinearAlgebra.Bridge.system_of_isSystemSolution
        _ _ _ (by native_decide)))
  catch e =>
    throwError "mathevidence linear algebra: system Bridge close failed \
(system_of_isSystemSolution; ME-RV-040). detail: {e.toMessageData}"

private def closeKernel (_eqProofs : Array Expr) : TacticM Unit := do
  let _ := _eqProofs
  try
    evalTactic (← `(tactic|
      refine MathEvidence.Checkers.LinearAlgebra.Bridge.kernel_of_isKernelVector
        _ _ (by native_decide)))
  catch e =>
    throwError "mathevidence linear algebra: kernel Bridge close failed \
(kernel_of_isKernelVector; ME-RV-040). detail: {e.toMessageData}"

private def closeDet (_eqProof : Expr) : TacticM Unit := do
  let _ := _eqProof
  -- Mathlib transport: general-n `det_of_isDetIdentity` (non-partial fuel detRats).
  try
    evalTactic (← `(tactic|
      refine MathEvidence.Checkers.LinearAlgebra.Bridge.det_of_isDetIdentity
        _ _ (by native_decide)))
  catch e =>
    throwError "mathevidence linear algebra: det Bridge close failed \
(det_of_isDetIdentity; ME-RV-040). detail: {e.toMessageData}"

/-- `mathevidence_linear_algebra` — Meta reify + IR gate + Bridge soundness. -/
elab "mathevidence_linear_algebra" : tactic => do
  let goal ← getMainGoal
  let goalType ← instantiateMVars (← goal.getType)
  -- Case: A * B = 1 ∧ B * A = 1  OR  kernel A.mulVec v = 0 ∧ v ≠ 0
  if let some (l, r) ← peelAnd? goalType then
    match ← matchMulVecEq l, ← matchNeZeroVec r with
    | some (A, v, rhs), some v' =>
      let rhs ← whnfR rhs
      unless ← isZeroVec rhs do
        throwError "{unsupportedMessage}\nreason: kernel residual is not zero"
      let A ← whnfR A; let v ← whnfR v; let v' ← whnfR v'
      unless v == v' do
        throwError "{unsupportedMessage}\nreason: kernel vector mismatch across ∧"
      match ← reifyLeanMatrixExprWithProof A, ← reifyLeanVectorExprWithProof v with
      | .ok RA, .ok RV =>
        unless isKernelVector RA.reified.matrix RV.vector do
          throwError "mathevidence linear algebra: isKernelVector failed on reified IR"
        closeKernel #[RA.eqProof, RV.eqProof]
      | .error err, _ =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | _, .error err =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
    | _, _ =>
      match ← matchMulEqOne l, ← matchMulEqOne r with
      | some (A1, B1), some (B2, A2) =>
        let A1 ← whnfR A1; let B1 ← whnfR B1; let A2 ← whnfR A2; let B2 ← whnfR B2
        unless A1 == A2 && B1 == B2 do
          throwError "{unsupportedMessage}\nreason: conjunct matrices do not match"
        match ← reifyLeanMatrixExprWithProof A1, ← reifyLeanMatrixExprWithProof B1 with
        | .ok RA, .ok RB =>
          unless isInverseWitness RA.reified.matrix RB.reified.matrix do
            throwError "mathevidence linear algebra: isInverseWitness failed on reified IR"
          closeTwoSidedInverse #[RA.eqProof, RB.eqProof]
        | .error err, _ =>
          throwError "{unsupportedMessage}\nreason: {Reject.format err}"
        | _, .error err =>
          throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | _, _ =>
        throwError "{unsupportedMessage}\nreason: And-goal arms are not mul-eq-one or kernel"
  else
    if let some (A, x, b) ← matchMulVecEq goalType then
      match ← reifyLeanMatrixExprWithProof A,
            ← reifyLeanVectorExprWithProof x,
            ← reifyLeanVectorExprWithProof b with
      | .ok RA, .ok RX, .ok RB =>
        unless isSystemSolution RA.reified.matrix RB.vector RX.vector do
          throwError "mathevidence linear algebra: isSystemSolution failed on reified IR"
        closeSystem #[RA.eqProof, RX.eqProof, RB.eqProof]
      | .error err, _, _ =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | _, .error err, _ =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | _, _, .error err =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
    else if let some (A, dExpr) ← matchDetEq goalType then
      match ← reifyLeanMatrixExprWithProof A with
      | .error err =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | .ok RA =>
        match ← reifyRatLit dExpr with
        | .error err =>
          throwError "{unsupportedMessage}\nreason: det RHS {Reject.format err}"
        | .ok d =>
          unless isDetIdentity RA.reified.matrix d do
            throwError "mathevidence linear algebra: isDetIdentity failed on reified IR"
          closeDet RA.eqProof
    else
      match ← matchMulEqOne goalType with
      | none =>
        let result ← reifyLeanMatrixExpr goalType
        match result with
        | .ok _ =>
          throwError "mathevidence linear algebra: reified a matrix type/value, but goal is not a supported shape"
        | .error err =>
          throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | some (A, B) =>
        match ← reifyLeanMatrixExprWithProof A, ← reifyLeanMatrixExprWithProof B with
        | .ok RA, .ok RB =>
          unless isRightInverse RA.reified.matrix RB.reified.matrix do
            throwError "mathevidence linear algebra: isRightInverse failed on reified IR"
          closeRightInverse #[RA.eqProof, RB.eqProof]
        | .error err, _ =>
          throwError "{unsupportedMessage}\nreason: {Reject.format err}"
        | _, .error err =>
          throwError "{unsupportedMessage}\nreason: {Reject.format err}"

end MathEvidence.Tactic.LinearAlgebra
