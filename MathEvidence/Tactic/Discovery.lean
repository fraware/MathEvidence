/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.Checkers.RationalEquality.Decode
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Checkers.RationalEquality.Replay
import MathEvidence.Checkers.RationalEquality.Wire
import MathEvidence.Core.Digest
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.EnvironmentLock
import MathEvidence.Core.ExprSerialize
import MathEvidence.Core.JsonCanonical
import MathEvidence.Tactic.RationalClose
import MathEvidence.Tactic.ReifyRational
import MathEvidence.Tactic.Status

/-!
# Discovery orchestration (CI-safe offline default)

Default: reify the goal, match committed offline fixtures, never spawn backends.
Live: when `MATHEVIDENCE_DISCOVERY=1` (or `true`/`live`), spawn the Python
discovery CLI which talks to adapters, writes a bundle, and returns certificate
JSON on stdout for Lean-side check.

After checker accept, closes via `replaySound` / Bridge (`eq_of_proposition`
or elaborated live `eq_of_replaySound`). `field_simp` may discharge denominator
side conditions only — never as independent equality authority (ME-RV-023).

On successful live Bridge close, emits Candidate Bundle + Certification Record
digests (v0.3 path, same binding discipline as kernel replay).
-/

namespace MathEvidence.Tactic.Discovery

open Lean Meta Elab Tactic
open MathEvidence.Core
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Checkers.RationalEquality.OfflineFixtures
open MathEvidence.Checkers.RationalEquality.Decode
open MathEvidence.Checkers.RationalEquality.Wire
open MathEvidence.Tactic
open MathEvidence.Tactic.ReifyRational
open MathEvidence.Tactic.RationalClose

abbrev RExpr := MathEvidence.IR.RationalExpr.Expr

/-- UTF-8 SHA-256 helper for live artifact binding digests. -/
def sha256Utf8 (s : String) : EvidenceId :=
  sha256Bytes s.toUTF8

/-- Emit Candidate Bundle + Certification Record digests after live Bridge close.

Same v0.3 binding discipline as kernel / tactic replay: theorem identity digests
are distinct from `requestDigest`; Candidate Bundle status stays `computed` in
the binding payload while the Certification Record reports `soundness_verified`.
-/
def emitLiveRationalArtifacts
    (req : Request) (_cert : Certificate) (goalType : Lean.Expr) : TacticM Unit := do
  let lock := EnvironmentLock.rationalEqualityDefault
  let envDig ←
    match lock.digest with
    | .ok d => pure d
    | .error e => throwError s!"live discovery: environment lock digest failed: {e}"
  let typeId ←
    try
      ExprSerialize.theoremTypeIdentityOfExpr goalType envDig
    catch _ =>
      pure {
        elaboratedSerialization := "mathevidence-live-theorem-identity"
        binders := req.claim.varNames.map fun n =>
          { name := n, kind := .default, typeSerialization := "Rat" }
        constantNames := ["Rat", "Eq"]
        environmentLockDigest := envDig
      }
  let thDig ←
    match typeId.digest with
    | .ok d => pure d
    | .error e => throwError s!"live discovery: theorem type digest failed: {e}"
  if thDig.value == req.requestDigest.value then
    throwError "live discovery: theorem digest collided with request digest (refusing)"
  let candBinding :=
    s!"candidate|v0.3|{envDig.value}|{req.requestDigest.value}|live-discovery"
  let candEid := sha256Utf8 candBinding
  let candDig : BundleDigest :=
    match BundleDigest.ofWire? candEid.value with
    | some d => d
    | none => ⟨candEid.value⟩
  if candDig.value == req.requestDigest.value then
    throwError "live discovery: candidate bundle digest collided with request digest"
  let certBinding :=
    s!"certification|v0.3|{candDig.value}|{thDig.value}|{req.requestDigest.value}|\
eq_of_replaySound"
  let certEid := sha256Utf8 certBinding
  let certDig : BundleDigest :=
    match BundleDigest.ofWire? certEid.value with
    | some d => d
    | none => ⟨certEid.value⟩
  logInfo m!"live Bridge close (ME-RV-023 / E-12): Candidate Bundle \
digest={candDig.value} Certification Record digest={certDig.value} \
theoremTypeDigest={thDig.value} requestDigest={req.requestDigest.value} \
assurance=kernel_replay result=soundness_verified \
authority=eq_of_replaySound (elaborated live Request/Certificate)"

/-- Bind `requestDigest` using Lean JCS (parity with Python). -/
def bindRequestDigest (c : Claim) : Except String (Json × RequestDigest) :=
  bindClaimDigest c

def discoveryEnabled : IO Bool := do
  match ← IO.getEnv "MATHEVIDENCE_DISCOVERY" with
  | some v =>
    let v := v.trim.toLower
    pure (v == "1" || v == "true" || v == "live" || v == "on")
  | none => pure false

/-- Map claim to a committed offline bundle when IR matches.

When several fixtures share the same IR, prefer one whose backend matches the
requested discovery backend (SymPy vs Mathematica). -/
def matchOfflineBundle (c : Claim) (prefer : Backend := .none) : Option BundleId :=
  let pairs : List (BundleId × Claim) := [
    (.basicSympy, claim_basic_sympy),
    (.basicMathematica, claim_basic_mathematica),
    (.validIdentity, claim_valid_identity),
    (.redundantCondition, claim_redundant_condition),
    (.variablePermutation, claim_variable_permutation),
    (.largeCoeffs, claim_large_coeffs)
  ]
  let hits := pairs.filter fun (_, cl) => claimsEqual c cl
  match prefer with
  | .mathematica =>
    (hits.find? fun (id, _) => id.backend == .mathematica).map (·.1)
      <|> hits.head?.map (·.1)
  | .sympy =>
    (hits.find? fun (id, _) => id.backend == .sympy).map (·.1)
      <|> hits.head?.map (·.1)
  | .none => hits.head?.map (·.1)

/-- Status report after successful reification without a live backend. -/
def offlineDiscoveryReport (c : Claim) (backend : Backend) : StatusReport :=
  match matchOfflineBundle c backend with
  | some id =>
    let report := replayStatus id
    { report with
      backend := backend
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

/-- Deprecated: no longer closes equality via `field_simp; ring`.

Authority close is `RationalClose.tryCloseViaFixtureAuthority`. -/
def tryCloseRationalEquality : TacticM Bool :=
  pure false

/-- Describe open goals for status reporting (claim vs remaining work). -/
def remainingGoalSummaries : TacticM (List String) := do
  let goals ← getGoals
  goals.mapM fun g => do
    let t ← g.withContext do
      let ty ← g.getType
      pure (toString (← ppExpr ty))
    pure s!"goal: {t}"

/-- Build a full status report (always includes claim requested vs established). -/
def makeStatusReport
    (_c : Claim)
    (backend : Backend)
    (claim : ClaimClass)
    (established : Option ClaimClass)
    (result : ResultStatus)
    (bundle : String)
    (conds : List String)
    (remaining : List String)
    (detail : String) : StatusReport :=
  { operation := .rationalEquality
    fragmentSupported := true
    assumptionsExported := conds.map fun d => s!"{d} ≠ 0"
    conditionsReturned := conds
    backend := backend
    claimRequested := claim
    claimEstablished := established
    resultStatus := result
    assuranceMode := .kernelReplay
    evidenceBundle := bundle
    remainingGoals := remaining
    detail := detail }

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
    | .ok { claim := c, fvars := fvars } =>
      let c := { c with claimClass := claim }
      let live ← discoveryEnabled
      if !live then
        let report0 := offlineDiscoveryReport c backend
        match matchOfflineBundle c backend with
        | some id =>
          let b := id.replayBundle
          unless checkBool b.request b.certificate do
            throwError "offline fixture failed checker after reify match"
          let conds := b.certificate.denomFactors.map fun e => reprStr e
          let closed ← tryCloseViaFixtureAuthority id fvars
          let remaining ← remainingGoalSummaries
          let report := makeStatusReport c (if backend == .none then id.backend else backend) claim
            (if closed then some .soundResult else none)
            (if closed then .soundnessVerified else .computed)
            id.toPath
            conds
            (if closed then [] else
              if remaining.isEmpty then
                conds.map fun d => s!"nonzero: {d}"
              else remaining)
            (if closed then
              s!"discovery(offline): reified; checker accepted {id.toPath}; \
closed via replaySound/Bridge (eq_of_proposition); side conditions from local hyps"
             else
              s!"discovery(offline): reified; checker accepted {id.toPath}; \
equality not closed via soundness bridge — add nonzero denom hyps then retry \
(no claim at poles; no independent field_simp;ring authority).\n(prior) {report0.detail}")
          logInfo m!"{report.format}"
          unless closed do
            throwError
              "mathevidence discovery(offline): fixture matched and checked, but soundness \
bridge could not finish the goal. Add nonzero denominator hypotheses, then retry \
or use `mathevidence replay`.\n{report.format}"
        | none =>
          let dens := (c.lhs.denominators ++ c.rhs.denominators).map reprStr
          let report := makeStatusReport c backend claim none .unsupported "" dens
            ["set MATHEVIDENCE_DISCOVERY=1 to spawn adapters, or commit a bundle and replay"]
            report0.detail
          logInfo m!"{report.format}"
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
            let expectedReq ←
              match Request.ofClaim c with
              | .ok r => pure r
              | .error e => throwError s!"live discovery: Request.ofClaim failed: {e}"
            unless cert.requestDigest == expectedReq.requestDigest do
              throwError "live discovery: certificate requestDigest does not match Lean-derived request"
            unless checkBool expectedReq cert do
              throwError "live discovery: Lean checker rejected certificate"
            let conds := cert.denomFactors.map fun e => reprStr e
            let closed ← tryCloseViaReplaySoundLive expectedReq cert fvars
            let remaining ← remainingGoalSummaries
            if closed then
              emitLiveRationalArtifacts expectedReq cert tgt
            let report := makeStatusReport c backend claim
              (if closed then some .soundResult else none)
              (if closed then .soundnessVerified else .computed)
              "(discovery ephemeral bundle)"
              conds
              (if closed then [] else
                if remaining.isEmpty then
                  conds.map fun d => s!"nonzero: {d}"
                else remaining)
              (if closed then
                "discovery(live): adapter spawned; checker accepted; closed via \
elaborated live eq_of_replaySound/Bridge; Candidate Bundle + Certification Record emitted"
               else
                "discovery(live): adapter spawned; checker accepted certificate; \
finish remaining side-condition goals via soundness bridge; no claim at poles")
            logInfo m!"{report.format}"
            unless closed do
              throwError
                "mathevidence discovery(live): checker accepted certificate; finish remaining \
side-condition goals via soundness bridge.\n{report.format}"

end MathEvidence.Tactic.Discovery
