/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import Mathlib.Tactic.FieldSimp
import MathEvidence.Checkers.RationalEquality.Bridge
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest.Types
import MathEvidence.IR.RationalExpr.Eval
import MathEvidence.Tactic.Status

/-!
# Close ℚ equality via `replaySound` / Bridge (ME-RV-023)

Authority path:

1. `checkBool` gate (already enforced by callers);
2. apply `eq_of_proposition` / `eq_of_replaySound` (built from `checkBool_sound`
   / fixture `sound_*`, or elaborated live `Request`/`Certificate`);
3. discharge denominator side conditions from local hypotheses (automation OK);
4. discharge IR-eval ↔ goal-side transport via `simp [eval]`.

`field_simp` / `ring` MUST NOT prove the original equality independently.
They MAY appear only while discharging side-condition / eval-transport goals.
-/

namespace MathEvidence.Tactic.RationalClose

open Lean Meta Elab Tactic
open MathEvidence.Core
open MathEvidence.IR.RationalExpr
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Checkers.RationalEquality.OfflineFixtures
open MathEvidence.Tactic

abbrev RExpr := MathEvidence.IR.RationalExpr.Expr

/-- Offline fixture → pre-proved `Claim.proposition` constant (authority). -/
def soundTheoremName? : BundleId → Option Name
  | .basicSympy => some ``sound_basic_sympy
  | .basicMathematica => some ``sound_basic_mathematica
  | .validIdentity => some ``sound_valid_identity
  | .redundantCondition => some ``sound_redundant_condition
  | .variablePermutation => some ``sound_variable_permutation
  | .largeCoeffs => some ``sound_large_coeffs
  | _ => none

/-- Offline fixture → `(req, cert)` for `eq_of_replaySound` fallback. -/
def reqCertNames? : BundleId → Option (Name × Name)
  | .basicSympy => some (``req_basic_sympy, ``cert_basic_sympy)
  | .basicMathematica => some (``req_basic_mathematica, ``cert_basic_mathematica)
  | .validIdentity => some (``req_valid_identity, ``cert_valid_identity)
  | .redundantCondition =>
      some (``req_redundant_condition, ``cert_redundant_condition)
  | .variablePermutation =>
      some (``req_variable_permutation, ``cert_variable_permutation)
  | .largeCoeffs => some (``req_large_coeffs, ``cert_large_coeffs)
  | _ => none

/-- Build `fun i : Nat => List.getD vals i (0 : ℚ)`. -/
def mkEnvFromFVars (fvars : Array Lean.Expr) : MetaM Lean.Expr := do
  let ratTy := Lean.mkConst ``_root_.Rat
  let zero ← mkAppOptM ``OfNat.ofNat #[some ratTy, some (mkNatLit 0), none]
  let vals ← mkListLit ratTy fvars.toList
  withLocalDeclD `i (Lean.mkConst ``Nat) fun i => do
    let body ← mkAppM ``List.getD #[vals, i, zero]
    mkLambdaFVars #[i] body

/-- Quote IR `Expr` as a concrete Lean term (live Bridge close). -/
partial def quoteRExpr (e : RExpr) : MetaM Lean.Expr := do
  match e with
  | .var i => mkAppM ``MathEvidence.IR.RationalExpr.Expr.var #[toExpr i]
  | .int n => mkAppM ``MathEvidence.IR.RationalExpr.Expr.int #[toExpr n]
  | .rat n d =>
    mkAppM ``MathEvidence.IR.RationalExpr.Expr.rat #[toExpr n, toExpr d]
  | .neg a => mkAppM ``MathEvidence.IR.RationalExpr.Expr.neg #[← quoteRExpr a]
  | .add a b =>
    mkAppM ``MathEvidence.IR.RationalExpr.Expr.add
      #[← quoteRExpr a, ← quoteRExpr b]
  | .sub a b =>
    mkAppM ``MathEvidence.IR.RationalExpr.Expr.sub
      #[← quoteRExpr a, ← quoteRExpr b]
  | .mul a b =>
    mkAppM ``MathEvidence.IR.RationalExpr.Expr.mul
      #[← quoteRExpr a, ← quoteRExpr b]
  | .pow b k =>
    mkAppM ``MathEvidence.IR.RationalExpr.Expr.pow #[← quoteRExpr b, toExpr k]
  | .div n d =>
    mkAppM ``MathEvidence.IR.RationalExpr.Expr.div
      #[← quoteRExpr n, ← quoteRExpr d]

def quoteRExprList (es : List RExpr) : MetaM Lean.Expr := do
  let ty := Lean.mkConst ``MathEvidence.IR.RationalExpr.Expr
  let quoted ← es.mapM quoteRExpr
  mkListLit ty quoted

def quoteClaimClass (c : ClaimClass) : Lean.Expr :=
  match c with
  | .candidate => mkConst ``ClaimClass.candidate
  | .witness => mkConst ``ClaimClass.witness
  | .refutation => mkConst ``ClaimClass.refutation
  | .decomposition => mkConst ``ClaimClass.decomposition
  | .soundResult => mkConst ``ClaimClass.soundResult
  | .completeSolution => mkConst ``ClaimClass.completeSolution
  | .optimum => mkConst ``ClaimClass.optimum
  | .enclosure => mkConst ``ClaimClass.enclosure
  | .canonicalForm => mkConst ``ClaimClass.canonicalForm

def quoteRequestDigest (d : RequestDigest) : MetaM Lean.Expr :=
  mkAppM ``RequestDigest.mk #[toExpr d.value]

def quoteCapabilityRef (c : CapabilityRef) : MetaM Lean.Expr := do
  if c == CapabilityRef.rationalEquality then
    pure (mkConst ``CapabilityRef.rationalEquality)
  else
    let idE ← mkAppM ``CapabilityId.mk #[toExpr c.id.id]
    let verE ← mkAppM ``CapabilityVersion.mk #[toExpr c.version.version]
    mkAppM ``CapabilityRef.mk #[idE, verE]

def quoteClaim (c : Claim) : MetaM Lean.Expr := do
  let names ← mkListLit (mkConst ``String) (c.varNames.map toExpr)
  let lhs ← quoteRExpr c.lhs
  let rhs ← quoteRExpr c.rhs
  let known ← quoteRExprList c.knownAssumptions
  let cc := quoteClaimClass c.claimClass
  mkAppM ``Claim.mk #[names, lhs, rhs, known, cc]

def quoteRequest (req : Request) : MetaM Lean.Expr := do
  let cap ← quoteCapabilityRef req.capability
  let claim ← quoteClaim req.claim
  let dig ← quoteRequestDigest req.requestDigest
  mkAppM ``Request.mk #[cap, claim, dig]

def quoteCertificate (cert : Certificate) : MetaM Lean.Expr := do
  let dig ← quoteRequestDigest cert.requestDigest
  let dens ← quoteRExprList cert.denomFactors
  mkAppM ``Certificate.mk #[dig, dens]

/-- Discharge Bridge side goals only (conditions + eval transport). -/
def dischargeBridgeSideGoals : TacticM Unit := do
  evalTactic (← `(tactic|
    all_goals (
      try (intro e he
           simp [MathEvidence.IR.RationalExpr.eval, List.mem_cons,
             List.mem_append, List.getD] at *
           try (refine And.intro ?_ ?_
                · trivial
                · refine ⟨?_, ?_, ?_⟩
                  · simp [MathEvidence.IR.RationalExpr.eval, List.getD]
                  · simp [MathEvidence.IR.RationalExpr.eval, List.getD]
                  · assumption))
      try (simp [MathEvidence.IR.RationalExpr.eval, List.getD]
           <;> try split_ifs
           <;> try field_simp [*]
           <;> try rfl
           <;> try assumption))))

/-- Apply `eq_of_proposition sound env` and discharge remaining Bridge goals. -/
def tryCloseWithSoundTheorem (soundName : Name) (fvars : Array Lean.Expr) : TacticM Bool := do
  let goalsBefore ← getGoals
  if goalsBefore.isEmpty then return true
  try
    let env ← mkEnvFromFVars fvars
    let soundE := Lean.mkConst soundName
    let g ← getMainGoal
    let subgoals ← g.withContext do
      let pf ← mkAppM ``eq_of_proposition #[soundE, env]
      g.apply pf
    setGoals subgoals
    dischargeBridgeSideGoals
    return (← getGoals).isEmpty
  catch _ =>
    setGoals goalsBefore
    return false

/-- Fallback: `eq_of_replaySound req cert (by native_decide) env`. -/
def tryCloseWithReplaySound (reqName certName : Name) (fvars : Array Lean.Expr) :
    TacticM Bool := do
  let goalsBefore ← getGoals
  if goalsBefore.isEmpty then return true
  try
    let env ← mkEnvFromFVars fvars
    let g ← getMainGoal
    let subgoals ← g.withContext do
      let reqE := Lean.mkConst reqName
      let certE := Lean.mkConst certName
      let checkTy ← mkAppM ``Eq #[
        ← mkAppM ``checkBool #[reqE, certE],
        Lean.mkConst ``Bool.true]
      let checkMvar ← mkFreshExprMVar (some checkTy) (userName := `hCheck)
      let pf ← mkAppM ``eq_of_replaySound #[reqE, certE, checkMvar, env]
      let gs ← g.apply pf
      pure (checkMvar.mvarId! :: gs)
    setGoals subgoals
    evalTactic (← `(tactic| native_decide))
    dischargeBridgeSideGoals
    return (← getGoals).isEmpty
  catch _ =>
    setGoals goalsBefore
    return false

/-- Live path: elaborate `Request`/`Certificate` values and apply `eq_of_replaySound`.

Authority is checker soundness (`checkBool` → `replaySound`), not an independent
final `field_simp; ring`. -/
def tryCloseWithLiveReplaySound
    (req : Request) (cert : Certificate) (fvars : Array Lean.Expr) : TacticM Bool := do
  let goalsBefore ← getGoals
  if goalsBefore.isEmpty then return true
  try
    let env ← mkEnvFromFVars fvars
    let g ← getMainGoal
    let subgoals ← g.withContext do
      let reqE ← quoteRequest req
      let certE ← quoteCertificate cert
      let checkTy ← mkAppM ``Eq #[
        ← mkAppM ``checkBool #[reqE, certE],
        Lean.mkConst ``Bool.true]
      let checkMvar ← mkFreshExprMVar (some checkTy) (userName := `hCheck)
      let pf ← mkAppM ``eq_of_replaySound #[reqE, certE, checkMvar, env]
      let gs ← g.apply pf
      pure (checkMvar.mvarId! :: gs)
    setGoals subgoals
    evalTactic (← `(tactic| native_decide))
    dischargeBridgeSideGoals
    return (← getGoals).isEmpty
  catch _ =>
    setGoals goalsBefore
    return false

/-- Apply a named Bridge closer; discharge residual goals by `assumption`. -/
def tryApplyCloser (closer : Name) : TacticM Bool := do
  let goalsBefore ← getGoals
  if goalsBefore.isEmpty then return true
  try
    let g ← getMainGoal
    let subgoals ← g.withContext do
      g.apply (mkConst closer)
    setGoals subgoals
    -- Side conditions (denom ≠ 0) come from the local context.
    evalTactic (← `(tactic| all_goals (try assumption)))
    if (← getGoals).isEmpty then
      return true
    setGoals goalsBefore
    return false
  catch _ =>
    setGoals goalsBefore
    return false

/-- Preferred close for offline fixtures: soundness theorem → Bridge. -/
def tryCloseViaFixtureAuthority (id : BundleId) (fvars : Array Lean.Expr) : TacticM Bool := do
  -- Protocol-reference / matching IR: apply concrete Bridge theorems first.
  -- These use `eq_of_proposition sound_*` as authority (ME-RV-023).
  let closers : List Name :=
    match id with
    | .basicSympy =>
      [``MathEvidence.Checkers.RationalEquality.close_basic_identity,
       ``MathEvidence.Checkers.RationalEquality.close_valid_identity]
    | .basicMathematica =>
      [``MathEvidence.Checkers.RationalEquality.close_basic_identity_mathematica,
       ``MathEvidence.Checkers.RationalEquality.close_basic_identity]
    | .validIdentity =>
      [``MathEvidence.Checkers.RationalEquality.close_valid_identity,
       ``MathEvidence.Checkers.RationalEquality.close_basic_identity]
    | _ => []
  for c in closers do
    if ← tryApplyCloser c then
      return true
  if let some sound := soundTheoremName? id then
    if ← tryCloseWithSoundTheorem sound fvars then
      return true
  if let some (reqN, certN) := reqCertNames? id then
    if ← tryCloseWithReplaySound reqN certN fvars then
      return true
  return false

/-- Close via fixture authority when digest matches, else live elaborated Bridge.

Live certificates (adapter discovery or synthesized) are closed by quoting the
concrete `Request`/`Certificate` and applying `eq_of_replaySound` — not by
fixture `Name` lookup alone (ME-RV-023 / E-12). -/
def tryCloseViaReplaySoundLive
    (req : Request) (cert : Certificate) (fvars : Array Lean.Expr) : TacticM Bool := do
  let pairs : List (BundleId × RequestDigest) := [
    (.basicSympy, digest_basic_sympy),
    (.basicMathematica, digest_basic_mathematica),
    (.validIdentity, digest_valid_identity),
    (.redundantCondition, digest_redundant_condition),
    (.variablePermutation, digest_variable_permutation),
    (.largeCoeffs, digest_large_coeffs)
  ]
  if let some (id, _) := pairs.find? fun (_, d) => d == req.requestDigest then
    if ← tryCloseViaFixtureAuthority id fvars then
      return true
  tryCloseWithLiveReplaySound req cert fvars

end MathEvidence.Tactic.RationalClose
