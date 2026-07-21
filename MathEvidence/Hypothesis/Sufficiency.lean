/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Certificate
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.Soundness
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.Checkers.RationalEquality.SpecProp
import MathEvidence.Core.Digest.Types
import MathEvidence.Hypothesis.Lattice

namespace MathEvidence.Hypothesis

open MathEvidence.IR.RationalExpr
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Core

/-!
# Sufficiency proof loop

Proposed condition sets become proof obligations under the existing
`RationalEquality` checker. Sufficiency requires **both** polynomial identity
(`polyOk`) and denominator coverage (`coverOk`) under a digest-bound certificate.
Coverage alone is never sufficiency.

`proveSufficient` returns a typed three-way result:
* `proved` — checker accept + soundness bridge available
* `failed` — checker reject with an explicit reason
* `unknown` — reserved for resource / unsupported shapes (not used by the
  default rational path, which always decides)
-/

/-- Typed citation fields for a sufficiency attempt (Lean + Agent facing). -/
structure SufficiencyEvidence where
  /-- Lean theorem / soundness decl that owns the claim when proved. -/
  theoremDecl : String := "MathEvidence.Hypothesis.sufficient_implies_proposition"
  /-- Checker entry decl that decided acceptance. -/
  checkerDecl : String := "MathEvidence.Checkers.RationalEquality.checkBool"
  /-- Optional receipt id / digest hex when a checker receipt is attached. -/
  receiptId : String := ""
  /-- Optional axiom-report artifact id (content digest or path token). -/
  axiomReportId : String := ""
  /-- Request digest wire string for binding. -/
  requestDigest : String := ""
  /-- Human-readable detail (reject reason or notes). -/
  detail : String := ""
  deriving DecidableEq, Repr, Inhabited

/-- Build an untrusted certificate binding `conditions` as denominator factors. -/
def certificateOf (req : Request) (conditions : List Expr) : Certificate where
  requestDigest := req.requestDigest
  denomFactors := conditions

/-- Executable sufficiency predicate: poly identity **and** denom coverage. -/
def isSufficient (req : Request) (conditions : List Expr) : Bool :=
  checkBool req (certificateOf req conditions)

/-- Denominator coverage alone (not sufficiency). -/
def denomCoverageOnly (req : Request) (conditions : List Expr) : Bool :=
  coverOk req (certificateOf req conditions)

/-- Polynomial identity alone (not sufficiency without coverage). -/
def polyIdentityOnly (req : Request) : Bool :=
  polyOk req

/-- Structured three-way result of a sufficiency attempt. -/
inductive SufficiencyResult where
  | proved (evidence : SufficiencyEvidence)
  | failed (evidence : SufficiencyEvidence)
  | unknown (evidence : SufficiencyEvidence)
  deriving DecidableEq, Repr, Inhabited

/-- Classify a rejected certificate into a typed failure detail. -/
def rejectDetail (req : Request) (cert : Certificate) : String :=
  if !digestOk req cert then
    "digest_mismatch"
  else if !wellFormedOk req cert then
    "ill_formed"
  else if !polyOk req then
    "poly_identity_failed"
  else if !coverOk req cert then
    "denom_coverage_incomplete"
  else
    "certificate_rejected"

/-- Default evidence scaffold bound to a request digest. -/
def evidenceOf (req : Request) (detail : String := "") : SufficiencyEvidence where
  requestDigest := req.requestDigest.value
  detail := detail

/-- Attach optional receipt / axiom-report ids to evidence. -/
def SufficiencyEvidence.withRefs
    (e : SufficiencyEvidence) (receiptId axiomReportId : String) : SufficiencyEvidence :=
  { e with receiptId := receiptId, axiomReportId := axiomReportId }

/-- Prove sufficiency via RationalEquality.checkBool; never from coverage alone. -/
def proveSufficient (req : Request) (conditions : List Expr)
    (receiptId : String := "") (axiomReportId : String := "") : SufficiencyResult :=
  let cert := certificateOf req conditions
  let base := (evidenceOf req).withRefs receiptId axiomReportId
  if checkBool req cert then
    .proved { base with detail := "checkBool_accept" }
  else
    .failed { base with detail := rejectDetail req cert }

/-- Boolean projection used by lattice builders. -/
def SufficiencyResult.isProved : SufficiencyResult → Bool
  | .proved _ => true
  | _ => false

/-- Extract evidence from any outcome. -/
def SufficiencyResult.evidence : SufficiencyResult → SufficiencyEvidence
  | .proved e => e
  | .failed e => e
  | .unknown e => e

/-- Soundness bridge: checker acceptance ⇒ claim proposition under `conditions`. -/
theorem sufficient_implies_proposition (req : Request) (conditions : List Expr)
    (h : isSufficient req conditions = true) :
    Claim.proposition req.claim conditions :=
  checkBool_sound req (certificateOf req conditions) h

/-- Record a proved sufficient set onto a lattice (by condition ids). -/
def ConditionLattice.recordSufficient
    (L : ConditionLattice) (ids : List String) (proved : Bool) : ConditionLattice :=
  if proved then
    { L with
      sufficientSets := L.sufficientSets ++ [ids]
      proposed := L.proposed.map fun n =>
        if ids.contains n.id then
          { n with status := .sufficientMember }
        else n }
  else L

end MathEvidence.Hypothesis
