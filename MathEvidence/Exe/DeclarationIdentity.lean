/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.Core.ExprSerialize

/-!
# `mathevidence-declaration-identity`

Loads one compiled module into a fresh Lean environment and reports the exact
stored theorem type, proof-term digest, and transitive axiom set for one
declaration.  This executable is intentionally downstream of elaboration: its
inputs identify *which* declaration to inspect, but theorem/proof identity is
computed only from `ConstantInfo` in the imported `Lean.Environment`.

This is the authority boundary used by generic Certification Records.  Python
or another orchestration layer may request an inspection; it may not supply the
theorem type or proof digest that the record will trust.
-/

open Lean
open MathEvidence.Core
open MathEvidence.Core.ExprSerialize

structure Config where
  moduleName : String
  declarationName : String
  environmentLockDigest : String
  deriving Repr

def usage : String :=
  "usage: mathevidence-declaration-identity --module <Module.Name> " ++
  "--declaration <Declaration.Name> --environment-lock-digest <sha256:...>"

partial def parseArgsAux
    (moduleName declarationName environmentLockDigest : Option String) :
    List String → Except String Config
  | [] =>
      match moduleName, declarationName, environmentLockDigest with
      | some m, some d, some e => .ok ⟨m, d, e⟩
      | _, _, _ => .error usage
  | "--module" :: value :: rest =>
      parseArgsAux (some value) declarationName environmentLockDigest rest
  | "--declaration" :: value :: rest =>
      parseArgsAux moduleName (some value) environmentLockDigest rest
  | "--environment-lock-digest" :: value :: rest =>
      parseArgsAux moduleName declarationName (some value) rest
  | "--help" :: _ => .error usage
  | flag :: _ => .error s!"unknown or incomplete argument: {flag}\n{usage}"

def parseArgs (args : List String) : Except String Config :=
  parseArgsAux none none none args

/-- Parse a dotted Lean name without relying on parser syntax. -/
def dottedName (s : String) : Name :=
  (s.splitOn ".").foldl (fun n part => Name.str n part) Name.anonymous

def jsonEscape (s : String) : String :=
  let escapeChar (c : Char) : String :=
    match c with
    | '"' => "\\\""
    | '\\' => "\\\\"
    | '\n' => "\\n"
    | '\r' => "\\r"
    | '\t' => "\\t"
    | _ => toString c
  String.join (s.toList.map escapeChar)

def jsonString (s : String) : String :=
  "\"" ++ jsonEscape s ++ "\""

partial def joinWith (sep : String) : List String → String
  | [] => ""
  | [x] => x
  | x :: xs => x ++ sep ++ joinWith sep xs

def stringArrayJson (xs : List String) : String :=
  "[" ++ joinWith "," (xs.map jsonString) ++ "]"

def binderJson (b : TheoremBinder) : String :=
  "{" ++ joinWith "," [
    "\"name\":" ++ jsonString b.name,
    "\"kind\":" ++ jsonString b.kind.toWire,
    "\"typeSerialization\":" ++ jsonString b.typeSerialization
  ] ++ "}"

def typeIdentityJson (identity : TheoremTypeIdentity) : String :=
  "{" ++ joinWith "," [
    "\"schemaVersion\":" ++ jsonString identity.schemaVersion,
    "\"serializerVersion\":" ++ jsonString identity.serializerVersion,
    "\"elaboratedSerialization\":" ++ jsonString identity.elaboratedSerialization,
    "\"universeParams\":" ++ stringArrayJson identity.universeParams,
    "\"binders\":[" ++ joinWith "," (identity.binders.map binderJson) ++ "]",
    "\"constantNames\":" ++ stringArrayJson identity.constantNames,
    "\"environmentLockDigest\":" ++ jsonString identity.environmentLockDigest.value
  ] ++ "}"

def collectAxiomsOf (env : Environment) (constName : Name) : Array Name :=
  let (_, state) := ((CollectAxioms.collect constName).run env).run {}
  state.axioms

def reportJson
    (moduleName : String)
    (declarationName : String)
    (identity : TheoremTypeIdentity)
    (typeDigest : TheoremDigest)
    (proofDigest : ContentDigest)
    (axioms : List String) : String :=
  "{" ++ joinWith "," [
    "\"schemaVersion\":\"0.3.0\"",
    "\"authority\":\"Lean.Environment ConstantInfo\"",
    "\"moduleName\":" ++ jsonString moduleName,
    "\"declarationName\":" ++ jsonString declarationName,
    "\"theoremTypeDigest\":" ++ jsonString typeDigest.value,
    "\"proofDeclarationDigest\":" ++ jsonString proofDigest.value,
    "\"environmentLockDigest\":" ++ jsonString identity.environmentLockDigest.value,
    "\"typeIdentity\":" ++ typeIdentityJson identity,
    "\"axioms\":" ++ stringArrayJson axioms
  ] ++ "}"

def main (args : List String) : IO UInt32 := do
  match parseArgs args with
  | .error e =>
      IO.eprintln e
      pure 2
  | .ok cfg =>
      try
        let some envLockDigest := ContentDigest.ofWire? cfg.environmentLockDigest
          | throw <| IO.userError "invalid --environment-lock-digest"
        let sysroot ← findSysroot
        initSearchPath sysroot
        let moduleName := dottedName cfg.moduleName
        let imports : Array Import := #[{ module := moduleName }]
        let env ← importModules imports {} 0
        let declarationName := dottedName cfg.declarationName
        let some info := env.find? declarationName
          | throw <| IO.userError s!"declaration not found: {cfg.declarationName}"
        let identity ←
          match theoremTypeIdentityOfClosedExpr info.type envLockDigest with
          | .ok value => pure value
          | .error e => throw <| IO.userError e
        let typeDigest ←
          match identity.digest with
          | .ok value => pure value
          | .error e => throw <| IO.userError e
        let proofDigest ←
          match proofTermDigestOfConstInEnv? env declarationName envLockDigest with
          | .ok (some value) => pure value
          | .ok none =>
              throw <| IO.userError s!"declaration has no stored proof value: {cfg.declarationName}"
          | .error e => throw <| IO.userError e
        let axioms := (collectAxiomsOf env declarationName).toList.map (·.toString)
        IO.println <| reportJson cfg.moduleName cfg.declarationName identity typeDigest proofDigest axioms
        pure 0
      catch e =>
        IO.eprintln s!"declaration identity inspection failed: {e}"
        pure 3