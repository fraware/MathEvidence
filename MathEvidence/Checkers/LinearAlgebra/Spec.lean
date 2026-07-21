/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.EvidenceId
import MathEvidence.IR.MatrixExpr.Ops
import MathEvidence.IR.MatrixExpr.Serialize
import MathEvidence.IR.MatrixExpr.Syntax

namespace MathEvidence.Checkers.LinearAlgebra

open MathEvidence.Core
open MathEvidence.IR.MatrixExpr

/-- Supported exact linear-algebra operations (Project Spec §11.2).

Completeness of a kernel basis, rank, or full solution family are **not**
included; those require separate stronger claim classes. -/
inductive Operation where
  | inverseWitness
  | systemSolution
  | kernelVector
  | detIdentity
  deriving DecidableEq, Repr, Inhabited

def Operation.toWire : Operation → String
  | .inverseWitness => "inverse_witness"
  | .systemSolution => "system_solution"
  | .kernelVector => "kernel_vector"
  | .detIdentity => "det_identity"

def Operation.ofWire? : String → Option Operation
  | "inverse_witness" => some .inverseWitness
  | "system_solution" => some .systemSolution
  | "kernel_vector" => some .kernelVector
  | "det_identity" => some .detIdentity
  | _ => none

/-- Mathematical claim for one exact linear-algebra operation. -/
structure Claim where
  operation : Operation
  matrix : Matrix
  /-- Right-hand side for `systemSolution` (ignored otherwise). -/
  rhs : Vector := []
  /-- Claimed determinant for `detIdentity`. -/
  claimedDet : Option RatLit := none
  claimClass : ClaimClass := .witness
  deriving DecidableEq, Repr, Inhabited

/-- Versioned request binding digest + claim. -/
structure Request where
  capability : CapabilityRef := .linearAlgebra
  claim : Claim
  requestDigest : RequestDigest
  deriving DecidableEq, Repr, Inhabited

/-- Build a request payload and its digest from a claim. -/
def Request.ofClaim (c : Claim) : Request :=
  let payload : RequestPayload := {
    operation := c.operation.toWire
    matrix := c.matrix
    rhs := c.rhs
    claimedDet := c.claimedDet
    claim := c.claimClass.toWire
  }
  { claim := c, requestDigest := payload.digest }

/-- Executable operation check (shared by checker and claim proposition). -/
def payloadOk (op : Operation) (A : Matrix) (rhs : Vector) (claimedDet : Option RatLit)
    (inverse : Option Matrix) (vector : Option Vector) : Bool :=
  match op with
  | .inverseWitness =>
    match inverse with
    | some B => isInverseWitness A B
    | none => false
  | .systemSolution =>
    match vector with
    | some x => isSystemSolution A rhs x
    | none => false
  | .kernelVector =>
    match vector with
    | some v => isKernelVector A v
    | none => false
  | .detIdentity =>
    match claimedDet with
    | some d => isDetIdentity A d
    | none => false

/-- Proposition established on success (witness-strength only). -/
def Claim.proposition (c : Claim) (inverse : Option Matrix) (vector : Option Vector) :
    Prop :=
  payloadOk c.operation c.matrix c.rhs c.claimedDet inverse vector = true

end MathEvidence.Checkers.LinearAlgebra
