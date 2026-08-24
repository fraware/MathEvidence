/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.JsonCanonical
import MathEvidence.Core.TheoremIdentity

/-!
# Elaborated Expr serialization for theorem identity (ME-RV-020)

Structural walk of Lean 4 kernel `Expr` / `Level` constructors for digest
inputs. This is **not** pretty-printing (`ppExpr`); binder kinds, universe
levels, and constant names participate explicitly.

Proof-term digests (ME-RV-020 remainder): when a declaration value is
available, `proofTermDigestOfConst?` walks the same structural `serializeExpr`
profile (not Lean-internal `Expr.hash`). Compiler-revision `Expr.hash`
stability remains unclaimed and must not be used for Certification Records.

The `*InEnv` / `*OfClosedExpr` helpers are deliberately pure over an already
loaded `Lean.Environment`.  They are used by the certification driver after a
generated replay module has been compiled and imported, so theorem/proof
identity is derived from the declaration Lean actually accepted rather than
from orchestration metadata describing what was intended.
-/

namespace MathEvidence.Core.ExprSerialize

open Lean Meta
open MathEvidence.Core
open MathEvidence.Core.JsonCanonical

/-- Structural Level serialization (kernel constructors). -/
partial def serializeLevel : Level → String
  | .zero => "0"
  | .succ u => s!"(succ {serializeLevel u})"
  | .max u v => s!"(max {serializeLevel u} {serializeLevel v})"
  | .imax u v => s!"(imax {serializeLevel u} {serializeLevel v})"
  | .param n => s!"(param {n})"
  | .mvar id => s!"(mvar {id.name})"

def binderKindOfInfo : BinderInfo → BinderKindWire
  | .default => .default
  | .implicit => .implicit
  | .strictImplicit => .strictImplicit
  | .instImplicit => .instImplicit

def binderKindTag : BinderKindWire → String
  | .default => "default"
  | .implicit => "implicit"
  | .strictImplicit => "strictImplicit"
  | .instImplicit => "instImplicit"

/-- Structural Expr serialization (kernel constructors + binders + universes). -/
partial def serializeExpr : Expr → String
  | .bvar i => s!"(bvar {i})"
  | .fvar fvarId => s!"(fvar {fvarId.name})"
  | .mvar mvarId => s!"(mvar {mvarId.name})"
  | .sort u => s!"(sort {serializeLevel u})"
  | .const n us =>
    let usS := String.intercalate " " (us.map serializeLevel)
    s!"(const {n} [{usS}])"
  | .app f a => s!"(app {serializeExpr f} {serializeExpr a})"
  | .lam n t b bi =>
    s!"(lam {n} {binderKindTag (binderKindOfInfo bi)} {serializeExpr t} {serializeExpr b})"
  | .forallE n t b bi =>
    s!"(forall {n} {binderKindTag (binderKindOfInfo bi)} {serializeExpr t} {serializeExpr b})"
  | .letE n t v b _ =>
    s!"(let {n} {serializeExpr t} {serializeExpr v} {serializeExpr b})"
  | .lit (.natVal n) => s!"(litNat {n})"
  | .lit (.strVal s) => s!"(litStr {s})"
  | .mdata _ e => s!"(mdata {serializeExpr e})"
  | .proj typeName idx e => s!"(proj {typeName} {idx} {serializeExpr e})"

/-- Collect universe parameter names appearing in an Expr. -/
partial def collectUniverseParams (e : Expr) : List String :=
  let rec goLevel : Level → List String
    | .zero => []
    | .succ u => goLevel u
    | .max u v => goLevel u ++ goLevel v
    | .imax u v => goLevel u ++ goLevel v
    | .param n => [n.toString]
    | .mvar _ => []
  let rec go : Expr → List String
    | .bvar _ | .fvar _ | .mvar _ | .lit _ => []
    | .sort u => goLevel u
    | .const _ us => us.foldl (fun acc u => acc ++ goLevel u) []
    | .app f a => go f ++ go a
    | .lam _ t b _ => go t ++ go b
    | .forallE _ t b _ => go t ++ go b
    | .letE _ t v b _ => go t ++ go v ++ go b
    | .mdata _ e => go e
    | .proj _ _ e => go e
  (go e).eraseDups

/-- Sorted constant names referenced by an Expr. -/
def collectConstantNames (e : Expr) : List String :=
  (e.getUsedConstants.toList.map (·.toString)).toArray.qsort (· < ·) |>.toList

/-- Top-level Pi binders of a closed declaration type, without introducing fvars.

Binder types are serialized in the de-Bruijn context in which they occur.  This
is intentionally a structural snapshot of the stored kernel expression.
-/
partial def collectTopLevelBinders : Expr → List TheoremBinder
  | .forallE n t body bi =>
      ({
        name := n.toString
        kind := binderKindOfInfo bi
        typeSerialization := serializeExpr t
      } : TheoremBinder) :: collectTopLevelBinders body
  | _ => []

/-- Build theorem identity directly from a closed declaration type in a loaded
kernel environment.  No pretty printer and no caller-supplied theorem text is
involved. -/
def theoremTypeIdentityOfClosedExpr
    (ty : Expr) (envLockDig : ContentDigest) : Except String TheoremTypeIdentity := do
  if ty.hasMVar then
    throw "mathevidence theorem identity: stored type contains metavariables"
  pure {
    elaboratedSerialization := serializeExpr ty
    universeParams := collectUniverseParams ty
    binders := collectTopLevelBinders ty
    constantNames := collectConstantNames ty
    environmentLockDigest := envLockDig
  }

/-- Digest the exact stored declaration type under an environment lock. -/
def theoremTypeDigestOfClosedExpr
    (ty : Expr) (envLockDig : ContentDigest) : Except String TheoremDigest := do
  let identity ← theoremTypeIdentityOfClosedExpr ty envLockDig
  identity.digest

/-- Build `TheoremTypeIdentity` from an elaborated type Expr + env lock digest. -/
def theoremTypeIdentityOfExpr (ty : Expr) (envLockDig : ContentDigest) :
    MetaM TheoremTypeIdentity := do
  let ty ← instantiateMVars ty
  -- Reject lingering metavariables in the type (not fully elaborated).
  if ty.hasMVar then
    throwError "mathevidence theorem identity: type still contains metavariables"
  forallTelescope ty fun xs _body => do
    let mut binders : Array TheoremBinder := #[]
    for x in xs do
      let ldecl ← x.fvarId!.getDecl
      let tSer := serializeExpr (← instantiateMVars ldecl.type)
      binders := binders.push {
        name := ldecl.userName.toString
        kind := binderKindOfInfo ldecl.binderInfo
        typeSerialization := tSer
      }
    pure {
      elaboratedSerialization := serializeExpr ty
      universeParams := collectUniverseParams ty
      binders := binders.toList
      constantNames := collectConstantNames ty
      environmentLockDigest := envLockDig
    }

/-- Digest an elaborated type Expr under an environment lock. -/
def theoremTypeDigestOfExpr (ty : Expr) (envLockDig : ContentDigest) :
    MetaM TheoremDigest := do
  let id ← theoremTypeIdentityOfExpr ty envLockDig
  match id.digest with
  | .ok d => pure d
  | .error e => throwError s!"mathevidence theorem identity: digest failed: {e}"

/-- Stable proof-term serialization from an explicitly supplied environment.
Returns `none` when the declaration has no stored value. -/
def proofTermSerializationOfConstInEnv?
    (env : Environment) (name : Name) : Except String (Option String) := do
  match env.find? name with
  | none => pure none
  | some info =>
    match info.value? with
    | none => pure none
    | some v =>
      if v.hasMVar then
        throw "mathevidence theorem identity: stored proof term contains metavariables"
      pure (some (serializeExpr v))

/-- Digest a proof term from the declaration value actually present in `env`. -/
def proofTermDigestOfConstInEnv?
    (env : Environment) (name : Name) (envLockDig : ContentDigest) :
    Except String (Option ContentDigest) := do
  match ← proofTermSerializationOfConstInEnv? env name with
  | none => pure none
  | some ser =>
    let payload := Json.mkObj [
      ("schemaVersion", Json.str theoremIdentitySchemaVersion),
      ("serializerVersion", Json.str theoremIdentitySerializerVersion),
      ("kind", Json.str "proofTerm"),
      ("declarationName", Json.str name.toString),
      ("elaboratedSerialization", Json.str ser),
      ("environmentLockDigest", Json.str envLockDig.value)
    ]
    match JsonCanonical.digest payload with
    | .ok eid =>
      match EvidenceId.toContentDigest eid with
      | some d => pure (some d)
      | none => throw "mathevidence proof-term digest wire form invalid"
    | .error e => throw s!"mathevidence proof-term digest failed: {e}"

/-- Stable proof-term serialization via the same kernel Expr walk (not `Expr.hash`).

Returns `none` when the constant has no stored value (e.g. axiom / opaque).
-/
def proofTermSerializationOfConst? (name : Name) : MetaM (Option String) := do
  let env ← getEnv
  match env.find? name with
  | none => pure none
  | some info =>
    match info.value? with
    | none => pure none
    | some v =>
      let v ← instantiateMVars v
      if v.hasMVar then
        throwError "mathevidence theorem identity: proof term still contains metavariables"
      pure (some (serializeExpr v))

/-- Digest binding for a proof term under the theorem-identity serializer profile. -/
def proofTermDigestOfConst? (name : Name) (envLockDig : ContentDigest) :
    MetaM (Option ContentDigest) := do
  match ← proofTermSerializationOfConst? name with
  | none => pure none
  | some ser =>
    let payload := Json.mkObj [
      ("schemaVersion", Json.str theoremIdentitySchemaVersion),
      ("serializerVersion", Json.str theoremIdentitySerializerVersion),
      ("kind", Json.str "proofTerm"),
      ("declarationName", Json.str name.toString),
      ("elaboratedSerialization", Json.str ser),
      ("environmentLockDigest", Json.str envLockDig.value)
    ]
    match JsonCanonical.digest payload with
    | .ok eid =>
      match EvidenceId.toContentDigest eid with
      | some d => pure (some d)
      | none => throwError "mathevidence proof-term digest wire form invalid"
    | .error e => throwError s!"mathevidence proof-term digest failed: {e}"

end MathEvidence.Core.ExprSerialize