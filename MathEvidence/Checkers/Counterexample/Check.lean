/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.Digest
import MathEvidence.Core.ErrorCode
import MathEvidence.Checkers.Counterexample.Certificate
import MathEvidence.Checkers.Counterexample.Spec
import MathEvidence.IR.FinitePredicate.Eval

namespace MathEvidence.Checkers.Counterexample

open MathEvidence.Core
open MathEvidence.IR.FinitePredicate

inductive CheckResult where
  | accept
  | reject (code : ErrorCode) (detail : String := "")
  deriving DecidableEq, Repr, Inhabited

def digestOk (req : Request) (cert : Certificate) : Bool :=
  cert.requestDigest == req.requestDigest

def wellFormedOk (req : Request) (cert : Certificate) : Bool :=
  decide (req.claim.varNames.length = req.claim.domains.length) &&
    domainsWellFormed req.claim.domains &&
    req.claim.pred.wellFormed req.claim.domains &&
    req.claim.pred.withinSizeLimit &&
    Assignment.wellFormed req.claim.domains cert.witness

def evalOk (req : Request) (cert : Certificate) : Bool :=
  isCounterexample cert.witness req.claim.pred

def checkBool (req : Request) (cert : Certificate) : Bool :=
  digestOk req cert && wellFormedOk req cert && evalOk req cert

def check (req : Request) (_cand : Candidate := {}) (cert : Certificate) : CheckResult :=
  if checkBool req cert then
    .accept
  else
    .reject .certificateRejected "finite counterexample check failed"

inductive SearchResult where
  | found (witness : Assignment)
  | unknown (detail : String := "")
  | reject (detail : String := "")
  deriving DecidableEq, Repr, Inhabited

private def intRange (lo hi : Int) : List Int :=
  if _h : lo ≤ hi then
    (List.range ((hi - lo).toNat + 1)).map fun k => lo + Int.ofNat k
  else
    []

private def Domain.values (ctx : Assignment) : Domain → Option (List Val)
  | ⟨.bool, _, _, _⟩ => some [.bool false, .bool true]
  | ⟨.nat, some b, none, none⟩ => some ((List.range (b + 1)).map Val.nat)
  | ⟨.nat, none, lo?, some hi⟩ =>
    match evalBoundAsInt ctx hi with
    | none => none
    | some upper =>
      let lower :=
        match lo? with
        | none => some 0
        | some lo => evalBoundAsInt ctx lo
      match lower with
      | none => none
      | some lower =>
        if lower ≤ upper then
          some ((intRange lower upper).filterMap fun i =>
            if i < 0 then none else some (.nat i.toNat))
        else
          some []
  | ⟨.int, some b, none, none⟩ =>
    some ((intRange (-(Int.ofNat b)) (Int.ofNat b)).map Val.int)
  | ⟨.int, none, some lo, some hi⟩ =>
    match evalBoundAsInt ctx lo, evalBoundAsInt ctx hi with
    | some lower, some upper => some ((intRange lower upper).map Val.int)
    | _, _ => none
  | _ => none

partial def searchFrom (pred : Pred) : List Domain → Assignment → Nat → SearchResult
  | _, _, 0 => .unknown "operational search budget exhausted"
  | [], ctx, _ =>
    if isCounterexample ctx pred then
      .found ctx
    else
      .unknown "finite search found no refuting witness; this is not a truth proof"
  | d :: ds, ctx, budget =>
    match Domain.values ctx d with
    | none => .reject "dependent domain bound could not be evaluated"
    | some values =>
      let rec loop : List Val → Nat → SearchResult
        | _, 0 => .unknown "operational search budget exhausted"
        | [], _ => .unknown "finite search found no refuting witness; this is not a truth proof"
        | v :: vs, fuel =>
          if v.inDomainWith ctx d then
            match searchFrom pred ds (ctx ++ [v]) (fuel - 1) with
            | .found w => .found w
            | .reject detail => .reject detail
            | .unknown _ => loop vs (fuel - 1)
          else
            loop vs (fuel - 1)
      loop values budget

/-- Best-effort finite enumeration. Exhaustion reports `unknown`, never truth. -/
def searchCounterexample (claim : Claim) (budget : Nat) : SearchResult :=
  if budget = 0 then
    .unknown "zero operational search budget"
  else if !(decide (claim.varNames.length = claim.domains.length)) ||
      !domainsWellFormed claim.domains ||
      !claim.pred.wellFormed claim.domains ||
      !claim.pred.withinSizeLimit then
    .reject "ill-formed finite counterexample claim"
  else
    searchFrom claim.pred claim.domains [] budget

@[simp] theorem check_accept_iff (req : Request) (cand : Candidate) (cert : Certificate) :
    check req cand cert = .accept ↔ checkBool req cert = true := by
  simp [check]

end MathEvidence.Checkers.Counterexample
