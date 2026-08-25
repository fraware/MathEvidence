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

The current serializer canonicalizes declaration identity from a **closed**
kernel expression. Top-level binder types therefore retain their de-Bruijn
representation instead of being replaced by elaborator-generated free-variable
identifiers. Free variables, expression metavariables, and universe metavariables
are rejected for Certification Record identity.

Variable-width string atoms are length-delimited, and kernel `Name` values are
serialized structurally. This prevents delimiter text inside identifiers or
string literals from creating ambiguous structural serializations.

Proof-term digests use the same closed structural walk when a declaration value
is available. Lean-internal `Expr.hash` stability is not claimed.
-/

namespace MathEvidence.Core.ExprSerialize

open Lean Meta
open MathEvidence.Core
open MathEvidence.Core.JsonCanonical

/-- Length-delimited string atom used inside the structural serialization.

The decimal length precedes the raw string payload. Delimiter characters inside
that payload therefore cannot be reassigned to an adjacent structural field.
-/
def serializeStringAtom (s : String) : String :=
  s!"{s.length}:{s}"

/-- Structural serialization of kernel `Name` constructors. -/
partial def serializeName : Name → String
  | .anonymous => "(nameAnon)"
  | .str prefix value =>
      s!"(nameStr {serializeName prefix} {serializeStringAtom value})"
  | .num prefix value => s!"(nameNum {serializeName prefix} {value})"

/-- Structural Level serialization (kernel constructors). -/
partial def serializeLevel : Level → String
  | .zero => "0"
  | .succ u => s!"(succ {serializeLevel u})"
  | .max u v => s!"(max {serializeLevel u} {serializeLevel v})"
  | .imax u v => s!"(imax {serializeLevel u} {serializeLevel v})"
  | .param n => s!"(param {serializeName n})"
  | .mvar id => s!"(mvar {serializeName id.name})"

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
  | .fvar fvarId => s!"(fvar {serializeName fvarId.name})"
  | .mvar mvarId => s!"(mvar {serializeName mvarId.name})"
  | .sort u => s!"(sort {serializeLevel u})"
  | .const n us =>
    let usS := String.intercalate " " (us.map serializeLevel)
    s!"(const {serializeName n} [{usS}])"
  | .app f a => s!"(app {serializeExpr f} {serializeExpr a})"
  | .lam n t b bi =>
    s!"(lam {serializeName n} {binderKindTag (binderKindOfInfo bi)} {serializeExpr t} {serializeExpr b})"
  | .forallE n t b bi =>
    s!"(forall {serializeName n} {binderKindTag (binderKindOfInfo bi)} {serializeExpr t} {serializeExpr b})"
  | .letE n t v b _ =>
    s!"(let {serializeName n} {serializeExpr t} {serializeExpr v} {serializeExpr b})"
  | .lit (.natVal n) => s!"(litNat {n})"
  | .lit (.strVal s) => s!"(litStr {serializeStringAtom s})"
  | .mdata _ e => s!"(mdata {serializeExpr e})"
  | .proj typeName idx e => s!"(proj {serializeName typeName} {idx} {serializeExpr e})"

/-- True when a universe level is not closed. -/
partial def levelContainsMVar : Level → Bool
  | .zero => false
  | .succ u => levelContainsMVar u
  | .max u v => levelContainsMVar u || levelContainsMVar v
  | .imax u v => levelContainsMVar u || levelContainsMVar v
  | .param _ => false
  | .mvar _ => true

/-- Reject elaborator-local identities from canonical declaration serialization.
Bound variables are allowed because they are bound by surrounding lambdas/Pis. -/
partial def exprContainsFreeOrMeta : Expr → Bool
  | .bvar _ => false
  | .fvar _ => true
  | .mvar _ => true
  | .sort u => levelContainsMVar u
  | .const _ us => us.any levelContainsMVar
  | .app f a => exprContainsFreeOrMeta f || exprContainsFreeOrMeta a
  | .lam _ t b _ => exprContainsFreeOrMeta t || exprContainsFreeOrMeta b
  | .forallE _ t b _ => exprContainsFreeOrMeta t || exprContainsFreeOrMeta b
  | .letE _ t v b _ =>
      exprContainsFreeOrMeta t || exprContainsFreeOrMeta v || exprContainsFreeOrMeta b
  | .lit _ => false
  | .mdata _ e => exprContainsFreeOrMeta e
  | .proj _ _ e => exprContainsFreeOrMeta e

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

Binder types are serialized in the de-Bruijn context in which they occur. This
is the canonical binder representation for serializer 0.4.
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
kernel environment. No pretty printer and no caller-supplied theorem text is
involved. -/
def theoremTypeIdentityOfClosedExpr
    (ty : Expr) (envLockDig : ContentDigest) : Except String TheoremTypeIdentity := do
  if exprContainsFreeOrMeta ty then
    throw "mathevidence theorem identity: declaration type is not closed"
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

/-- MetaM compatibility wrapper for a closed elaborated declaration type.

After metavariable instantiation it delegates to the same closed-expression
canonicalization used by the environment inspector. Open goal expressions with
free variables are intentionally rejected as declaration identities.
-/
def theoremTypeIdentityOfExpr (ty : Expr) (envLockDig : ContentDigest) :
    MetaM TheoremTypeIdentity := do
  let ty ← instantiateMVars ty
  match theoremTypeIdentityOfClosedExpr ty envLockDig with
  | .ok identity => pure identity
  | .error e => throwError e

/-- Digest a closed elaborated declaration type under an environment lock. -/
def theoremTypeDigestOfExpr (ty : Expr) (envLockDig : ContentDigest) :
    MetaM TheoremDigest := do
  let identity ← theoremTypeIdentityOfExpr ty envLockDig
  match identity.digest with
  | .ok digest => pure digest
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
    | some value =>
      if exprContainsFreeOrMeta value then
        throw "mathevidence theorem identity: stored proof term is not closed"
      pure (some (serializeExpr value))

/-- Digest a proof term from the declaration value actually present in `env`. -/
def proofTermDigestOfConstInEnv?
    (env : Environment) (name : Name) (envLockDig : ContentDigest) :
    Except String (Option ContentDigest) := do
  match ← proofTermSerializationOfConstInEnv? env name with
  | none => pure none
  | some serialization =>
    let payload := Json.mkObj [
      ("schemaVersion", Json.str theoremIdentitySchemaVersion),
      ("serializerVersion", Json.str theoremIdentitySerializerVersion),
      ("kind", Json.str "proofTerm"),
      ("declarationName", Json.str name.toString),
      ("elaboratedSerialization", Json.str serialization),
      ("environmentLockDigest", Json.str envLockDig.value)
    ]
    match JsonCanonical.digest payload with
    | .ok evidenceId =>
      match EvidenceId.toContentDigest evidenceId with
      | some digest => pure (some digest)
      | none => throw "mathevidence proof-term digest wire form invalid"
    | .error e => throw s!"mathevidence proof-term digest failed: {e}"

/-- Stable proof-term serialization via the same closed kernel Expr walk. -/
def proofTermSerializationOfConst? (name : Name) : MetaM (Option String) := do
  let env ← getEnv
  match proofTermSerializationOfConstInEnv? env name with
  | .ok value => pure value
  | .error e => throwError e

/-- Digest binding for a proof term under the current theorem-identity serializer. -/
def proofTermDigestOfConst? (name : Name) (envLockDig : ContentDigest) :
    MetaM (Option ContentDigest) := do
  let env ← getEnv
  match proofTermDigestOfConstInEnv? env name envLockDig with
  | .ok value => pure value
  | .error e => throwError e

end MathEvidence.Core.ExprSerialize
