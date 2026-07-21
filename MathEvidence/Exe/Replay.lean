/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.Decode
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.Checkers.RationalEquality.Wire
import MathEvidence.Core.AssuranceMode
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.JsonCanonical
import MathEvidence.Core.ResultStatus

/-!
# `mathevidence-replay`

Offline theorem-producing replay for content-addressed evidence bundles.

Pipeline (hard-fail before any `claimEstablished`):

1. Resolve bundle path / content-addressed id
2. Verify manifest file content digests
3. Decode request + certificate (`.cjson` preferred, `.json` accepted)
4. Recompute request digest via Lean wire (`Request.ofClaim`)
5. Run rational `checkBool` (checker authority)
6. Match optional `--goal-file` claim to the request claim
7. Emit a structural checker receipt with `claimEstablished` only on full success

Python packaging remains preview/`tested` only; this exe is the Lean authority
Agent/Studio must consult for verified status on rational equality reference cases.
-/

open Lean
open MathEvidence.Core
open MathEvidence.Core.JsonCanonical
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Checkers.RationalEquality.Decode

def usage : String :=
  "usage: mathevidence-replay --bundle <path-or-store-id> [--goal-file <file>] [--store-root <dir>]"

partial def getFlag (name : String) : List String → Option String
  | [] => none
  | n :: v :: rest => if n == name && !v.isEmpty then some v else getFlag name rest
  | _ :: rest => getFlag name rest

/-- Resolve content-addressed `sha256_<hex>` under `storeRoot/sha256/<aa>/<rest>/`. -/
def resolveContentAddressed (storeRoot : System.FilePath) (bundleId : String) :
    Option System.FilePath :=
  if !bundleId.startsWith "sha256_" then none
  else
    let hex := bundleId.drop "sha256_".length
    if hex.length != 64 then none
    else
      let aa := hex.take 2
      let rest := hex.drop 2
      some (storeRoot / "sha256" / aa / rest)

/-- Prefer an existing filesystem path; else resolve under evidence store. -/
def resolveBundlePath (bundleArg : String) (storeRoot : System.FilePath) :
    IO System.FilePath := do
  let asPath := System.FilePath.mk bundleArg
  if (← asPath.pathExists) then
    return asPath
  match resolveContentAddressed storeRoot bundleArg with
  | some p =>
    if (← p.pathExists) then return p
    else
      throw <| IO.userError s!"bundle_not_found: content-addressed id {bundleArg}"
  | none =>
    throw <| IO.userError s!"bundle_not_found: {bundleArg}"

def contentDigestOfFile (path : System.FilePath) : IO String := do
  let bytes ← IO.FS.readBinFile path
  pure (sha256Bytes bytes).value

/-- First existing relative role path under the bundle (v0.2 `.cjson` then v0.1 `.json`). -/
def findRoleFile (bundle : System.FilePath) (stem : String) : IO (Option System.FilePath) := do
  let cjson := bundle / s!"{stem}.cjson"
  if (← cjson.pathExists) then return some cjson
  let json := bundle / s!"{stem}.json"
  if (← json.pathExists) then return some json
  return none

/-- Verify one manifest `files[]` entry. -/
def verifyFileEntry (bundle : System.FilePath) (entry : Json) : IO (Except String Unit) := do
  match entry.getObjValAs? String "path", entry.getObjValAs? String "digest" with
  | .ok rel, .ok expected =>
    if rel.isEmpty || (rel.splitOn "..").length > 1 then
      return .error s!"bundle_path_forbidden: {rel}"
    let path := bundle / rel
    if !(← path.pathExists) then
      return .error s!"content_digest_mismatch: missing file {rel}"
    let actual ← contentDigestOfFile path
    if actual != expected then
      return .error s!"content_digest_mismatch: {rel}: {actual} != {expected}"
    return .ok ()
  | _, _ =>
    return .error "manifest_schema_invalid: files entry missing path/digest"

def verifyManifestFiles (bundle : System.FilePath) (manifest : Json) : IO (Except String Nat) := do
  match manifest.getObjVal? "files" with
  | .error _ => return .error "manifest_schema_invalid: missing files"
  | .ok filesJson =>
    match filesJson.getArr? with
    | .error _ => return .error "manifest_schema_invalid: files not array"
    | .ok arr =>
      let mut n := 0
      for entry in arr do
        match ← verifyFileEntry bundle entry with
        | .error e => return .error e
        | .ok () => n := n + 1
      return .ok n

def requestDigestOf (manifest : Json) : String :=
  match manifest.getObjValAs? String "requestDigest" with
  | .ok d => d
  | .error _ => ""

/-- Structural claim match used for goal binding (independent of tactic Meta). -/
def claimsMatch (a b : Claim) : Bool :=
  a.varNames == b.varNames && a.lhs == b.lhs && a.rhs == b.rhs

def failExit (code : UInt32) (msg : String) : IO UInt32 := do
  IO.eprintln s!"mathevidence-replay: {msg}"
  pure code

def exitForError (err : String) : UInt32 :=
  if err.startsWith "bundle_not_found" then 2
  else if err.startsWith "manifest_schema_invalid" then 3
  else if err.startsWith "content_digest_mismatch" then 4
  else if err.startsWith "bundle_path_forbidden" then 5
  else if err.startsWith "request_digest_mismatch" then 6
  else if err.startsWith "certificate_decode_failed" then 7
  else if err.startsWith "certificate_rejected" then 8
  else if err.startsWith "goal_mismatch" then 9
  else if err.startsWith "capability_version_unsupported" then 10
  else 1

def receiptJson
    (req : Request)
    (bundleDig : String)
    (theoremDig : String)
    (detail : String) : Json :=
  Json.mkObj [
    ("schemaVersion", Json.str "0.2.0"),
    ("requestDigest", Json.str req.requestDigest.value),
    ("bundleDigest", Json.str bundleDig),
    ("theoremDigest", Json.str theoremDig),
    ("axiomDigests", Json.arr #[]),
    ("capability", Json.mkObj [
      ("id", Json.str req.capability.id.id),
      ("version", Json.str req.capability.version.version)
    ]),
    ("checker", Json.mkObj [
      ("package", Json.str "MathEvidence.Checkers.RationalEquality"),
      ("module", Json.str "MathEvidence.Checkers.RationalEquality.Check"),
      ("name", Json.str "checkBool"),
      ("version", Json.str "0.1.0"),
      ("soundnessTheorem", Json.str "checkBool_sound")
    ]),
    ("claimRequested", Json.str req.claim.claimClass.toWire),
    ("claimEstablished", Json.str ClaimClass.soundResult.toWire),
    ("unresolvedObligations", Json.arr #[]),
    ("assuranceMode", Json.str AssuranceMode.kernelReplay.toWire),
    ("resultStatus", Json.str ResultStatus.soundnessVerified.toWire),
    ("toolchain", Json.mkObj [
      ("leanVersion", Json.str "leanprover/lean4:v4.14.0"),
      ("lakeVersion", Json.str "lake"),
      ("mathlibVersion", Json.str "v4.14.0")
    ]),
    ("contentDigestsVerified", Json.bool true),
    ("detail", Json.str detail)
  ]

def decodeGoalClaim (goalRaw : String) : Except String Claim := do
  match decodeRequestString goalRaw with
  | .ok g => pure g.claim
  | .error _ =>
    match Json.parse goalRaw with
    | .error e => throw s!"goal JSON parse failed: {e}"
    | .ok j =>
      match decodeClaim j with
      | .ok c => pure c
      | .error e => throw s!"cannot decode goal claim: {e}"

/-- Digests + decode + check + optional goal match; emit receipt only on full success. -/
def theoremReplayRational
    (bundle : System.FilePath)
    (manifest : Json)
    (goalFile : Option System.FilePath)
    (bundleArg : String)
    (nFiles : Nat) : IO UInt32 := do
  let reqPath? ← findRoleFile bundle "request"
  let certPath? ← findRoleFile bundle "certificate"
  match reqPath?, certPath? with
  | none, _ =>
    failExit (exitForError "certificate_decode_failed")
      "certificate_decode_failed: missing request.cjson/request.json"
  | _, none =>
    failExit (exitForError "certificate_decode_failed")
      "certificate_decode_failed: missing certificate.cjson/certificate.json"
  | some reqPath, some certPath =>
    let reqRaw ← IO.FS.readFile reqPath
    let certRaw ← IO.FS.readFile certPath
    match decodeRequestString reqRaw with
    | .error e =>
      failExit (exitForError "certificate_decode_failed")
        s!"certificate_decode_failed: request: {e}"
    | .ok req =>
      if req.capability.id.id != "algebra.rational_equality" then
        failExit (exitForError "capability_version_unsupported")
          s!"capability_version_unsupported: {req.capability.id.id}"
      else
        match decodeCertificateString certRaw req.claim.varNames with
        | .error e =>
          failExit (exitForError "certificate_decode_failed")
            s!"certificate_decode_failed: certificate: {e}"
        | .ok cert =>
          let expected := Request.ofClaim req.claim
          if req.requestDigest != expected.requestDigest then
            failExit (exitForError "request_digest_mismatch")
              s!"request_digest_mismatch: wire={req.requestDigest.value} recomputed={expected.requestDigest.value}"
          else if cert.requestDigest != expected.requestDigest then
            failExit (exitForError "request_digest_mismatch")
              "request_digest_mismatch: certificate.requestDigest != recomputed request digest"
          else
            let manDig := requestDigestOf manifest
            if !(manDig == expected.requestDigest.value || manDig.isEmpty) then
              failExit (exitForError "request_digest_mismatch")
                "request_digest_mismatch: manifest.requestDigest != recomputed request digest"
            else if !checkBool expected cert then
              failExit (exitForError "certificate_rejected")
                "certificate_rejected: rational checkBool failed"
            else
              let goalOk : IO (Except String Unit) := do
                match goalFile with
                | none => pure (.ok ())
                | some gf =>
                  if !(← gf.pathExists) then
                    pure (.error s!"goal_mismatch: missing goal file {gf}")
                  else
                    let goalRaw ← IO.FS.readFile gf
                    match decodeGoalClaim goalRaw with
                    | .error e => pure (.error s!"goal_mismatch: {e}")
                    | .ok goalClaim =>
                      if claimsMatch goalClaim expected.claim then
                        pure (.ok ())
                      else
                        pure (.error
                          "goal_mismatch: goal claim does not match committed request claim")
              match ← goalOk with
              | .error e => failExit (exitForError e) e
              | .ok () =>
                let manPath ← do
                  match ← findRoleFile bundle "manifest" with
                  | some p => pure p
                  | none => pure (bundle / "manifest.json")
                let bundleDig ← contentDigestOfFile manPath
                let theoremDig := expected.requestDigest.value
                let detail :=
                  s!"theorem replay accepted for rational equality bundle {bundleArg}; filesVerified={nFiles}"
                let receipt := receiptJson expected bundleDig theoremDig detail
                match canonicalString receipt with
                | .error e =>
                  failExit 1 s!"checker_receipt_invalid: canonicalization failed: {e}"
                | .ok receiptText =>
                  IO.FS.writeFile (bundle / "checker-receipt.cjson") receiptText
                  IO.println receiptText
                  IO.eprintln
                    "mathevidence-replay: soundness_verified; claimEstablished=soundResult (Lean checker authority)"
                  pure 0

def main (args : List String) : IO UInt32 := do
  match getFlag "--bundle" args with
  | none =>
    IO.eprintln usage
    pure 1
  | some bundleArg =>
    let storeRoot :=
      System.FilePath.mk <|
        (getFlag "--store-root" args).getD "evidence/store"
    try
      let bundle ← resolveBundlePath bundleArg storeRoot
      let manifestPath? ← findRoleFile bundle "manifest"
      match manifestPath? with
      | none =>
        failExit 2 s!"bundle_not_found: missing manifest under {bundle}"
      | some manifestPath =>
        let raw ← IO.FS.readFile manifestPath
        match Json.parse raw with
        | .error err =>
          failExit 3 s!"manifest_schema_invalid: {err}"
        | .ok manifest =>
          match ← verifyManifestFiles bundle manifest with
          | .error err =>
            failExit (exitForError err) err
          | .ok nFiles =>
            let goal :=
              match getFlag "--goal-file" args with
              | some g => some (System.FilePath.mk g)
              | none => none
            let capId :=
              match manifest.getObjVal? "capability" with
              | .ok cap =>
                match cap.getObjValAs? String "id" with
                | .ok id => id
                | .error _ => ""
              | .error _ => ""
            if capId == "algebra.rational_equality" || capId.isEmpty then
              theoremReplayRational bundle manifest goal bundleArg nFiles
            else
              let reqDig := requestDigestOf manifest
              let tested :=
                Json.mkObj [
                  ("schemaVersion", Json.str "0.2.0"),
                  ("resultStatus", Json.str "tested"),
                  ("contentDigestsVerified", Json.bool true),
                  ("filesVerified", Json.num nFiles),
                  ("requestDigest", Json.str reqDig),
                  ("bundlePath", Json.str bundle.toString),
                  ("bundleId", Json.str bundleArg),
                  ("claimEstablished", Json.null),
                  ("detail", Json.str
                    "content digests verified; theorem-producing replay supports algebra.rational_equality")
                ]
              match canonicalString tested with
              | .ok s =>
                IO.println s
                IO.eprintln "mathevidence-replay: content digests ok (non-rational; tested only)"
                pure 0
              | .error e =>
                failExit 1 s!"checker_receipt_invalid: {e}"
    catch e =>
      let msg := toString e
      if msg.startsWith "bundle_not_found" then
        failExit 2 msg
      else
        failExit 2 s!"bundle_not_found: {e}"
