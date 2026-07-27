/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Checkers.RationalEquality.ReplaySound
import MathEvidence.Checkers.RationalEquality.Wire
import MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures
import MathEvidence.Checkers.AnalyticCalculus.ReplaySound
import MathEvidence.Core.AssuranceMode
import MathEvidence.Core.JsonCanonical
import MathEvidence.Core.ResultStatus

/-!
# `mathevidence-kernel-replay`

Theorem-producing kernel replay executable (Wave 2 / ME-RV-022 + ME-RV-054).

Compiled fixtures:

* rational `basic_sympy` (`certified_rational_replay_basic_sympy`)
* analytic product rule (`certified_analytic_replay_product_exe`)

CLI:

* `--self-test` — rational fixture Certification Record envelope
* `--self-test-analytic` — analytic product fixture envelope
* `--bundle <path>` — rational protocol-reference digest gate only
-/

open Lean
open MathEvidence.Core
open MathEvidence.Core.JsonCanonical
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Checkers.RationalEquality.OfflineFixtures
open MathEvidence.Checkers.AnalyticCalculus
open MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures

/-- Kernel-accepted rational replay for the protocol-reference fixture. -/
theorem certified_rational_replay_basic_sympy :
    Claim.proposition req_basic_sympy.claim cert_basic_sympy.denomFactors :=
  replaySound
    req_basic_sympy
    cert_basic_sympy
    (by native_decide : checkBool req_basic_sympy cert_basic_sympy = true)

#print axioms certified_rational_replay_basic_sympy

/-- Analytic product-rule fixture compiled into the exe (ME-RV-054). -/
theorem certified_analytic_replay_product_exe (x : ℝ) :
    HasDerivAt cert_product.source.interpret
      (cert_product.derivative.interpret x) x :=
  MathEvidence.Checkers.AnalyticCalculus.certified_analytic_replay_product x

#print axioms certified_analytic_replay_product_exe

namespace MathEvidence.Exe.KernelReplay

def usage : String :=
  "usage: mathevidence-kernel-replay (--self-test | --self-test-analytic | --bundle <path>) [--out <file>]"

partial def getFlag (name : String) : List String → Option String
  | [] => none
  | n :: v :: rest => if n == name && !v.isEmpty then some v else getFlag name rest
  | _ :: rest => getFlag name rest

def hasFlag (name : String) : List String → Bool
  | [] => false
  | n :: rest => n == name || hasFlag name rest

def allowedAxioms : List String :=
  ["propext", "Quot.sound", "Classical.choice", "Lean.ofReduceBool", "Lean.trustCompiler"]

def certificationEnvelope : Json :=
  let reqDig := req_basic_sympy.requestDigest.value
  Json.mkObj [
    ("schemaVersion", Json.str "0.3.0"),
    ("artifactKind", Json.str "certification"),
    ("ok", Json.bool true),
    ("resultStatus", Json.str ResultStatus.soundnessVerified.toWire),
    ("assuranceMode", Json.str AssuranceMode.kernelReplay.toWire),
    ("claimEstablished", Json.str "soundResult"),
    ("capability", Json.str "algebra.rational_equality"),
    ("declarationName", Json.str "certified_rational_replay_basic_sympy"),
    ("requestDigest", Json.str reqDig),
    ("soundnessTheorem", Json.str "replaySound"),
    ("checker", Json.mkObj [
      ("package", Json.str "MathEvidence.Checkers.RationalEquality"),
      ("module", Json.str "MathEvidence.Checkers.RationalEquality.ReplaySound"),
      ("name", Json.str "replaySound"),
      ("version", Json.str "0.3.0"),
      ("soundnessTheorem", Json.str "replaySound")
    ]),
    ("axiomPolicy", Json.mkObj [
      ("status", Json.str "compiled"),
      ("allowedAxioms", Json.arr (allowedAxioms.map Json.str).toArray),
      ("notes", Json.str
        "Axioms of certified_rational_replay_basic_sympy were printed at compile time (#print axioms).")
    ]),
    ("detail", Json.str
      "mathevidence-kernel-replay: kernel-accepted replaySound on OfflineFixtures.basic_sympy")
  ]

def analyticCertificationEnvelope : Json :=
  Json.mkObj [
    ("schemaVersion", Json.str "0.3.0"),
    ("artifactKind", Json.str "certification"),
    ("ok", Json.bool true),
    ("resultStatus", Json.str ResultStatus.soundnessVerified.toWire),
    ("assuranceMode", Json.str AssuranceMode.kernelReplay.toWire),
    ("claimEstablished", Json.str "soundResult"),
    ("capability", Json.str "analysis.analytic_calculus"),
    ("declarationName", Json.str "certified_analytic_replay_product"),
    ("requestDigest", Json.str "offline_fixture:analytic_cert_product"),
    ("soundnessTheorem", Json.str "replaySound"),
    ("checker", Json.mkObj [
      ("package", Json.str "MathEvidence.Checkers.AnalyticCalculus"),
      ("module", Json.str "MathEvidence.Checkers.AnalyticCalculus.ReplaySound"),
      ("name", Json.str "replaySound"),
      ("version", Json.str "0.3.0"),
      ("soundnessTheorem", Json.str "replaySound")
    ]),
    ("axiomPolicy", Json.mkObj [
      ("status", Json.str "compiled"),
      ("allowedAxioms", Json.arr (allowedAxioms.map Json.str).toArray),
      ("notes", Json.str
        "Axioms of certified_analytic_replay_product were printed at compile time (#print axioms).")
    ]),
    ("detail", Json.str
      "mathevidence-kernel-replay: kernel-accepted analytic replaySound on OfflineFixtures.cert_product")
  ]

def writeOut (path? : Option String) (text : String) : IO Unit := do
  match path? with
  | some p => IO.FS.writeFile p text
  | none => IO.println text

def failExit (code : UInt32) (msg : String) : IO UInt32 := do
  IO.eprintln s!"mathevidence-kernel-replay: {msg}"
  pure code

def readBundleRequestDigest (bundle : System.FilePath) : IO (Option String) := do
  let man := bundle / "manifest.cjson"
  let man2 := bundle / "manifest.json"
  let path ←
    if (← man.pathExists) then pure man
    else if (← man2.pathExists) then pure man2
    else return none
  let raw ← IO.FS.readFile path
  match Json.parse raw with
  | .error _ => pure none
  | .ok j =>
    match j.getObjValAs? String "requestDigest" with
    | .ok d => pure (some d)
    | .error _ => pure none

def emitSuccess (outPath : Option String) (envelope : Json) (detail : String) : IO UInt32 := do
  match canonicalString envelope with
  | .error e => failExit 1 s!"certification_canonicalization_failed: {e}"
  | .ok text =>
    writeOut outPath text
    IO.eprintln detail
    pure 0

def main (args : List String) : IO UInt32 := do
  if hasFlag "--help" args || hasFlag "-h" args then
    IO.println usage
    return 0
  let outPath := getFlag "--out" args
  if hasFlag "--self-test-analytic" args then
    if !(checkDeriv cert_product) then
      return ← failExit 8 "certificate_rejected: analytic cert_product checkDeriv failed"
    return ← emitSuccess outPath analyticCertificationEnvelope
      "mathevidence-kernel-replay: soundness_verified (replaySound / certified_analytic_replay_product)"
  if hasFlag "--self-test" args then
    if !(checkBool req_basic_sympy cert_basic_sympy) then
      return ← failExit 8 "certificate_rejected: basic_sympy checkBool failed"
    return ← emitSuccess outPath certificationEnvelope
      "mathevidence-kernel-replay: soundness_verified (replaySound / certified_rational_replay_basic_sympy)"
  match getFlag "--bundle" args with
  | none =>
    IO.eprintln usage
    pure 1
  | some bundleArg =>
    let bundle := System.FilePath.mk bundleArg
    if !(← bundle.pathExists) then
      return ← failExit 2 s!"bundle_not_found: {bundleArg}"
    let expected := req_basic_sympy.requestDigest.value
    match ← readBundleRequestDigest bundle with
    | none =>
      failExit 11
        "theorem_elaboration_failed: missing manifest.requestDigest; \
general bundles require adapters.common.kernel_replay + generate_replay_module.py"
    | some dig =>
      if dig != expected then
        failExit 11
          s!"theorem_elaboration_failed: bundle requestDigest {dig} is not the \
protocol-reference fixture ({expected}); use adapters.common.kernel_replay"
      else if !(checkBool req_basic_sympy cert_basic_sympy) then
        failExit 8 "certificate_rejected: basic_sympy checkBool failed"
      else
        emitSuccess outPath certificationEnvelope
          "mathevidence-kernel-replay: soundness_verified (replaySound / certified_rational_replay_basic_sympy)"

end MathEvidence.Exe.KernelReplay

def main (args : List String) : IO UInt32 :=
  MathEvidence.Exe.KernelReplay.main args
