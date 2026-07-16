/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring
import MathEvidence.Checkers.RationalEquality.Decode
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Checkers.RationalEquality.Replay
import MathEvidence.Core.JsonCanonical
import MathEvidence.Tactic.ReifyRational
import MathEvidence.Tactic.Status

/-!
# Discovery orchestration (CI-safe offline default)

Default: reify the goal, match committed offline fixtures, never spawn backends.
Live: when `MATHEVIDENCE_DISCOVERY=1` (or `true`/`live`), spawn the Python
discovery CLI which talks to adapters, writes a bundle, and returns certificate
JSON on stdout for Lean-side check.
-/

namespace MathEvidence.Tactic.Discovery

open Lean Meta Elab Tactic
open MathEvidence.Core
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Checkers.RationalEquality.OfflineFixtures
open MathEvidence.Checkers.RationalEquality.Decode
open MathEvidence.Tactic
open MathEvidence.Tactic.ReifyRational

abbrev RExpr := MathEvidence.IR.RationalExpr.Expr

/-- Serialize IR expr to adapter wire JSON (name-based). -/
partial def exprToWireJson (names : List String) : RExpr → Json
  | .var i =>
    let name := names.getD i s!"v{i}"
    Json.mkObj [("tag", Json.str "var"), ("name", Json.str name)]
  | .int n => Json.mkObj [("tag", Json.str "int"), ("value", Json.str (toString n))]
  | .rat n d =>
    Json.mkObj
      [("tag", Json.str "rat"), ("n", Json.str (toString n)), ("d", Json.num d)]
  | .neg e => Json.mkObj [("tag", Json.str "neg"), ("arg", exprToWireJson names e)]
  | .add a b =>
    Json.mkObj
      [("tag", Json.str "add"), ("left", exprToWireJson names a),
       ("right", exprToWireJson names b)]
  | .sub a b =>
    Json.mkObj
      [("tag", Json.str "sub"), ("left", exprToWireJson names a),
       ("right", exprToWireJson names b)]
  | .mul a b =>
    Json.mkObj
      [("tag", Json.str "mul"), ("left", exprToWireJson names a),
       ("right", exprToWireJson names b)]
  | .pow b k =>
    Json.mkObj
      [("tag", Json.str "pow"), ("base", exprToWireJson names b), ("exp", Json.num k)]
  | .div n d =>
    Json.mkObj
      [("tag", Json.str "div"), ("num", exprToWireJson names n),
       ("den", exprToWireJson names d)]

def varDeclJson (name : String) : Json :=
  Json.mkObj [("name", Json.str name), ("type", Json.str "Rat")]

/-- Build adapter request JSON (pre-digest) from a claim. -/
def claimToRequestJson (c : Claim) : Json :=
  Json.mkObj [
    ("schemaVersion", Json.str "0.1.0"),
    ("capability", Json.str "algebra.rational_equality"),
    ("capabilityVersion", Json.str "0.1.0"),
    ("variables", Json.arr (c.varNames.map varDeclJson).toArray),
    ("lhs", exprToWireJson c.varNames c.lhs),
    ("rhs", exprToWireJson c.varNames c.rhs),
    ("knownAssumptions", Json.arr #[]),
    ("requestedClaim", Json.str c.claimClass.toWire),
    ("resourcePolicy",
      Json.mkObj
        [("maxWallTimeMs", Json.num (10000 : Nat)),
         ("maxOutputBytes", Json.num (1048576 : Nat))])
  ]

/-- Bind `requestDigest` using Lean JCS (parity with Python). -/
def bindRequestDigest (c : Claim) : Except String (Json × EvidenceId) := do
  let j := claimToRequestJson c
  let d ← match JsonCanonical.digestRequestBinding j with
    | .ok d => pure d
    | .error e => throw e.toString
  let j' :=
    match j with
    | .obj m => Json.obj (m.insert compare "requestDigest" (Json.str d.value))
    | other => other
  pure (j', d)

def discoveryEnabled : IO Bool := do
  match ← IO.getEnv "MATHEVIDENCE_DISCOVERY" with
  | some v =>
    let v := v.trim.toLower
    pure (v == "1" || v == "true" || v == "live" || v == "on")
  | none => pure false

/-- Map claim to a committed offline bundle when IR matches. -/
def matchOfflineBundle (c : Claim) : Option BundleId :=
  let pairs : List (BundleId × Claim) := [
    (.basicSympy, claim_basic_sympy),
    (.basicMathematica, claim_basic_mathematica),
    (.validIdentity, claim_valid_identity),
    (.redundantCondition, claim_redundant_condition),
    (.variablePermutation, claim_variable_permutation),
    (.largeCoeffs, claim_large_coeffs)
  ]
  (pairs.find? fun (_, cl) => claimsEqual c cl).map (·.1)

/-- Status report after successful reification without a live backend. -/
def offlineDiscoveryReport (c : Claim) (backend : Backend) : StatusReport :=
  match matchOfflineBundle c with
  | some id =>
    let report := replayStatus id
    { report with
      detail :=
        s!"discovery(offline): reified claim matched committed bundle {id.toPath}; " ++
          "backends not started" }
  | none =>
    { operation := .rationalEquality
      fragmentSupported := true
      assumptionsExported := []
      conditionsReturned :=
        (c.lhs.denominators ++ c.rhs.denominators).map reprStr
      backend := backend
      claimRequested := c.claimClass
      claimEstablished := none
      resultStatus := .unsupported
      assuranceMode := .kernelReplay
      evidenceBundle := ""
      remainingGoals :=
        ["set MATHEVIDENCE_DISCOVERY=1 to spawn adapters, or commit a bundle and replay"]
      detail :=
        "discovery(offline): Rat equality reified; no matching fixture; backends not started. " ++
          "Run: python scripts/mathevidence_cli.py discover --backend sympy --request <req.json>" }

/-- Spawn Python discovery CLI via a temp request file; returns certificate JSON. -/
def spawnDiscover (requestJson : String) (backend : String) : IO (Except String String) := do
  let root ← IO.currentDir
  let script := root / "scripts" / "mathevidence_cli.py"
  unless ← script.pathExists do
    return .error s!"missing discovery CLI at {script}"
  let (handle, reqPath) ← IO.FS.createTempFile
  handle.putStr requestJson
  handle.flush
  let out ← IO.Process.output {
    cmd := "python"
    args := #[
      script.toString,
      "discover",
      "--backend", backend,
      "--request", reqPath.toString,
      "--emit-certificate",
      "--direct"
    ]
    cwd := root
  }
  try IO.FS.removeFile reqPath catch _ => pure ()
  if out.exitCode != 0 then
    return .error s!"discovery CLI failed (exit {out.exitCode}): {out.stderr}"
  let lines := out.stdout.splitOn "\n" |>.filter (fun s => !s.trim.isEmpty)
  match lines.getLast? with
  | some line => pure (.ok line)
  | none => pure (.error "discovery CLI produced empty stdout")

/-- Attempt `field_simp; ring` close; return true if main goal became `True` or solved. -/
def tryCloseRationalEquality : TacticM Bool := do
  let goalsBefore ← getGoals
  try
    evalTactic (← `(tactic| try field_simp <;> try ring))
  catch _ =>
    pure ()
  let goalsAfter ← getGoals
  if goalsAfter.isEmpty then
    return true
  if goalsAfter.length < goalsBefore.length then
    return true
  let g ← getMainGoal
  let t ← g.getType
  return t.isConstOf ``True

/-- Run discovery for the main goal: reify → offline match or live spawn → check. -/
def runDiscoveryOrchestration (backend : Backend) (claim : ClaimClass) : TacticM Unit := do
  let goal ← getMainGoal
  goal.withContext do
    let tgt ← goal.getType
    if tgt.isConstOf ``True then
      let report := discoveryStatus backend claim
      logInfo m!"{report.format}"
      throwError
        "mathevidence discovery: goal is `True` (status-only). For Rat equality goals, \
reification + offline fixture match or MATHEVIDENCE_DISCOVERY=1 applies.\n{report.format}"
    match ← reifyEqualityGoal tgt with
    | .error err =>
      throwError "mathevidence discovery: reification failed: {Reject.format err}"
    | .ok { claim := c, .. } =>
      let c := { c with claimClass := claim }
      let live ← discoveryEnabled
      if !live then
        let report := offlineDiscoveryReport c backend
        logInfo m!"{report.format}"
        match matchOfflineBundle c with
        | some id =>
          let b := id.replayBundle
          unless checkBool b.request b.certificate do
            throwError "offline fixture failed checker after reify match"
          let closed ← tryCloseRationalEquality
          if closed then
            logInfo m!"discovery(offline): closed after matching {id.toPath}"
          else
            throwError
              "mathevidence discovery(offline): fixture matched and checked, but automatic \
close did not finish the goal. Add nonzero denominator hypotheses then \
`field_simp; ring`, or use `mathevidence replay`.\n{report.format}"
        | none =>
          throwError
            "mathevidence discovery(offline): reified Rat equality; backends not started \
(CI-safe default). Set MATHEVIDENCE_DISCOVERY=1 to spawn adapters, or generate a \
bundle with scripts/mathevidence_cli.py discover then `mathevidence replay`.\n\
{report.format}"
      else
        let backendStr :=
          match backend with
          | .mathematica => "mathematica"
          | .sympy | .none => "sympy"
        match bindRequestDigest c with
        | .error e => throwError "digest bind failed: {e}"
        | .ok (reqJ, _) =>
          let reqText := reqJ.compress
          let certText ← match ← spawnDiscover reqText backendStr with
            | .ok t => pure t
            | .error e => throwError "{e}"
          match decodeCertificateString certText c.varNames with
          | .error e => throwError "certificate decode failed: {e}"
          | .ok cert =>
            let req := { Request.ofClaim c with requestDigest := cert.requestDigest }
            unless checkBool req cert do
              throwError "live discovery: Lean checker rejected certificate"
            let conds := cert.denomFactors.map fun e => reprStr e
            let report : StatusReport := {
              operation := .rationalEquality
              fragmentSupported := true
              assumptionsExported := []
              conditionsReturned := conds
              backend := backend
              claimRequested := claim
              claimEstablished := some .soundResult
              resultStatus := .soundnessVerified
              assuranceMode := .kernelReplay
              evidenceBundle := "(discovery ephemeral bundle)"
              remainingGoals := conds.map fun d => s!"nonzero: {d}"
              detail := "discovery(live): adapter spawned; certificate checked"
            }
            logInfo m!"{report.format}"
            let closed ← tryCloseRationalEquality
            unless closed do
              throwError
                "mathevidence discovery(live): certificate accepted; finish remaining \
nonzero/equality goals (field_simp/ring).\n{report.format}"

end MathEvidence.Tactic.Discovery
