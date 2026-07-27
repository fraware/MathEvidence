/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean

/-!
# `mathevidence-axiom-report` (ME-RV-072)

Environment-level axiom audit: loads trusted MathEvidence package roots via
`Lean.importModules`, then:

1. Flags any `ConstantInfo.axiomInfo` whose defining module is under
   `MathEvidence.*` (project-specific axioms).
2. Runs `CollectAxioms` on a fixed set of soundness / bridge theorems and
   records transitive imported axioms (classical / propext / quot markers).
3. Keeps a source scan for `sorry` / `admit` / `unsafe` as defense-in-depth.
-/

open Lean

structure Finding where
  file : String
  line : Nat
  kind : String
  pattern : String
  severity : String
  deriving Repr

def usage : String :=
  "usage: mathevidence-axiom-report [--output <path>]"

def normalizePath (path : String) : String :=
  path.replace "\\" "/"

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

def containsSubstr (haystack needle : String) : Bool :=
  (haystack.splitOn needle).length > 1

partial def joinWith (sep : String) : List String → String
  | [] => ""
  | [x] => x
  | x :: xs => x ++ sep ++ joinWith sep xs

/-- Trusted package entry modules (olean-backed; avoid barrel roots that may lag). -/
def trustedRoots : Array Name := #[
  `MathEvidence.Core.Basic,
  `MathEvidence.IR.MatrixExpr.Ops,
  `MathEvidence.Encoding.Matrix,
  `MathEvidence.Checkers.LinearAlgebra.Bridge,
  `MathEvidence.Checkers.RationalEquality.Soundness,
  `MathEvidence.Checkers.IdealMembership.Soundness,
  `MathEvidence.Checkers.Counterexample.Soundness
]

/-- Soundness / bridge declarations whose transitive axioms are reported. -/
def auditedDecls : Array Name := #[
  `MathEvidence.Checkers.RationalEquality.Soundness.checkBool_sound,
  `MathEvidence.Checkers.LinearAlgebra.Bridge.system_of_isSystemSolution,
  `MathEvidence.Checkers.LinearAlgebra.Bridge.det_of_isDetIdentity,
  `MathEvidence.Checkers.LinearAlgebra.Bridge.det_of_isDetIdentity_fin3,
  `MathEvidence.Checkers.LinearAlgebra.Bridge.det_of_isDetIdentity_fin4,
  `MathEvidence.Checkers.LinearAlgebra.Bridge.det_of_isDetIdentity_fin5,
  `MathEvidence.Checkers.Counterexample.Soundness.checkBool_sound,
  `MathEvidence.Checkers.IdealMembership.Soundness.checkBool_sound,
  `MathEvidence.Checkers.IdealMembership.Soundness.mem_span_pair_of_check
]

def isMathEvidenceModule (n : Name) : Bool :=
  let s := n.toString
  s == "MathEvidence" || s.startsWith "MathEvidence."

/-- Skip equation-compiler / specialization / hygiene axioms (not user `axiom`). -/
def isGeneratedAxiomName (n : Name) : Bool :=
  let s := n.toString
  containsSubstr s "._at." || containsSubstr s "._hyg" || containsSubstr s "._spec_" ||
    containsSubstr s "._aux_" || containsSubstr s "@" || s.startsWith "_private." ||
    containsSubstr s ".proof_" || containsSubstr s "match_"

def collectAxiomsOf (env : Environment) (constName : Name) : Array Name :=
  let (_, s) := ((CollectAxioms.collect constName).run env).run {}
  s.axioms

/-- User-facing project axioms whose home module is under MathEvidence. -/
def projectAxiomFindings (env : Environment) : List Finding :=
  Id.run do
    let mut out : List Finding := []
    for (name, info) in env.constants.toList do
      match info with
      | .axiomInfo _ =>
        if isGeneratedAxiomName name then
          pure ()
        else
          match env.getModuleIdxFor? name with
          | some idx =>
            let mod := env.header.moduleNames[idx.toNat]!
            if isMathEvidenceModule mod then
              out := out ++ [{
                file := mod.toString
                line := 0
                kind := "project_axiom_env"
                pattern := name.toString
                severity := "error"
              }]
          | none =>
            pure ()
      | _ => pure ()
    pure out

structure DeclAxiomReport where
  declaration : String
  importedAxioms : Array String
  deriving Repr

def declAxiomReports (env : Environment) : Array DeclAxiomReport × List Finding :=
  Id.run do
    let mut reports : Array DeclAxiomReport := #[]
    let mut findings : List Finding := []
    for decl in auditedDecls do
      if env.contains decl then
        let axs := collectAxiomsOf env decl
        let axStrs := axs.map (·.toString)
        reports := reports.push { declaration := decl.toString, importedAxioms := axStrs }
        -- Fail if transitive axioms include sorryAx
        if axStrs.any (fun s => containsSubstr s "sorryAx") then
          findings := findings ++ [{
            file := decl.toString
            line := 0
            kind := "sorryAx_env"
            pattern := "sorryAx"
            severity := "error"
          }]
      else
        reports := reports.push {
          declaration := decl.toString
          importedAxioms := #["<declaration_not_in_environment>"]
        }
    pure (reports, findings)

/-- Source-scan defense-in-depth (sorry/admit/unsafe). -/
partial def stripBlockCommentsAux : List Char → Nat → List Char
  | [], _ => []
  | '/' :: '-' :: rest, depth =>
      ' ' :: ' ' :: stripBlockCommentsAux rest (depth + 1)
  | '-' :: '/' :: rest, depth =>
      if depth == 0 then
        '-' :: '/' :: stripBlockCommentsAux rest 0
      else
        ' ' :: ' ' :: stripBlockCommentsAux rest (depth - 1)
  | c :: rest, depth =>
      if depth == 0 then
        c :: stripBlockCommentsAux rest depth
      else if c == '\n' then
        '\n' :: stripBlockCommentsAux rest depth
      else
        ' ' :: stripBlockCommentsAux rest depth

def stripBlockComments (text : String) : String :=
  String.mk (stripBlockCommentsAux text.toList 0)

partial def stripStringLiteralsAux : List Char → Bool → List Char
  | [], _ => []
  | '"' :: rest, false =>
      ' ' :: stripStringLiteralsAux rest true
  | '\\' :: escaped :: rest, true =>
      ' ' :: (if escaped == '\n' then '\n' else ' ') :: stripStringLiteralsAux rest true
  | '"' :: rest, true =>
      ' ' :: stripStringLiteralsAux rest false
  | c :: rest, true =>
      (if c == '\n' then '\n' else ' ') :: stripStringLiteralsAux rest true
  | c :: rest, false =>
      c :: stripStringLiteralsAux rest false

def stripStringLiterals (text : String) : String :=
  String.mk (stripStringLiteralsAux text.toList false)

def stripLineComment (line : String) : String :=
  match line.splitOn "--" with
  | [] => line
  | first :: _ => first

def cleanedLines (text : String) : List String :=
  (stripStringLiterals (stripBlockComments text)).splitOn "\n" |>.map stripLineComment

def isLeanFile (path : System.FilePath) : Bool :=
  normalizePath path.toString |>.endsWith ".lean"

partial def collectLeanFiles (dir : System.FilePath) : IO (List System.FilePath) := do
  let entries ←
    try dir.readDir
    catch _ => pure #[]
  let mut files : List System.FilePath := []
  for entry in entries do
    if ← entry.path.isDir then
      files := files ++ (← collectLeanFiles entry.path)
    else if isLeanFile entry.path then
      files := files ++ [entry.path]
  pure files

def isTrustedUnsafePath (file : String) : Bool :=
  file.startsWith "MathEvidence/Core/"
    || file == "MathEvidence/Core.lean"
    || file.startsWith "MathEvidence/IR/"
    || file == "MathEvidence/IR.lean"
    || file.startsWith "MathEvidence/Encoding/"
    || file == "MathEvidence/Encoding.lean"
    || file.startsWith "MathEvidence/Checkers/"
    || file == "MathEvidence/Checkers.lean"

def hasAxiomDeclaration (line : String) : Bool :=
  let t := line.trim
  t.startsWith "axiom " || t.startsWith "axiom\t"

def scanLine (file : String) (lineNumber : Nat) (line : String) : List Finding :=
  let findings : List Finding := []
  let findings :=
    if containsSubstr line "sorryAx" then
      findings ++ [{ file, line := lineNumber, kind := "sorryAx", pattern := "sorryAx", severity := "error" }]
    else
      findings
  let findings :=
    if !containsSubstr line "sorryAx" && containsSubstr line "sorry" then
      findings ++ [{ file, line := lineNumber, kind := "incomplete_proof", pattern := "sorry", severity := "error" }]
    else
      findings
  let findings :=
    if containsSubstr line "admit" then
      findings ++ [{ file, line := lineNumber, kind := "incomplete_proof", pattern := "admit", severity := "error" }]
    else
      findings
  let findings :=
    if hasAxiomDeclaration line then
      findings ++ [{ file, line := lineNumber, kind := "project_axiom", pattern := "axiom", severity := "error" }]
    else
      findings
  let findings :=
    if isTrustedUnsafePath file && containsSubstr line "unsafe" then
      findings ++ [{ file, line := lineNumber, kind := "unauthorized_unsafe", pattern := "unsafe", severity := "error" }]
    else
      findings
  findings

partial def scanLines (file : String) : List String → Nat → List Finding
  | [], _ => []
  | line :: rest, lineNumber =>
      scanLine file lineNumber line ++ scanLines file rest (lineNumber + 1)

def findingJson (finding : Finding) : String :=
  "{" ++ joinWith "," [
    "\"file\":" ++ jsonString finding.file,
    "\"line\":" ++ toString finding.line,
    "\"kind\":" ++ jsonString finding.kind,
    "\"pattern\":" ++ jsonString finding.pattern,
    "\"severity\":" ++ jsonString finding.severity
  ] ++ "}"

def declReportJson (r : DeclAxiomReport) : String :=
  "{" ++ joinWith "," [
    "\"declaration\":" ++ jsonString r.declaration,
    "\"importedAxioms\":[" ++
      joinWith "," (r.importedAxioms.toList.map jsonString) ++ "]"
  ] ++ "}"

def classicalMarkers (reports : Array DeclAxiomReport) : Array String :=
  Id.run do
    let mut markers : Array String := #[]
    for r in reports do
      for a in r.importedAxioms do
        if a == "propext" || a == "Classical.choice" || a == "Quot.sound" ||
            containsSubstr a "propext" || containsSubstr a "Classical" ||
            containsSubstr a "Quot.sound" then
          if !markers.contains a then
            markers := markers.push a
    pure markers

def reportJson
    (modulesLoaded : Nat)
    (declReports : Array DeclAxiomReport)
    (findings : List Finding) : String :=
  let markers := classicalMarkers declReports
  "{" ++ joinWith "," [
    "\"tool\":\"mathevidence-axiom-report\"",
    "\"status\":" ++ jsonString (if findings.isEmpty then "pass" else "fail"),
    "\"scanMode\":\"Lean.Environment importModules + CollectAxioms + source defense-in-depth\"",
    "\"environmentLevel\":true",
    "\"authority\":\"Lean Environment ConstantInfo / CollectAxioms over trusted roots\"",
    "\"modulesLoaded\":" ++ toString modulesLoaded,
    "\"declarationAxiomReports\":[" ++
      joinWith "," (declReports.toList.map declReportJson) ++ "]",
    "\"classicalPropextQuotientMarkers\":[" ++
      joinWith "," (markers.toList.map jsonString) ++ "]",
    "\"policy\":{\"failOn\":[\"sorryAx\",\"sorry\",\"admit\",\"project_axiom\",\"project_axiom_env\",\"unauthorized_unsafe_in_Core_IR_Encoding_Checkers\"]}",
    "\"violations\":[" ++ joinWith "," (findings.map findingJson) ++ "]"
  ] ++ "}"

partial def parseArgs : List String → Except String (Option System.FilePath)
  | [] => Except.ok none
  | "--output" :: path :: rest =>
      match parseArgs rest with
      | Except.ok none => Except.ok (some path)
      | Except.ok (some _) => Except.error "multiple --output paths provided"
      | Except.error e => Except.error e
  | "-o" :: path :: rest =>
      match parseArgs rest with
      | Except.ok none => Except.ok (some path)
      | Except.ok (some _) => Except.error "multiple output paths provided"
      | Except.error e => Except.error e
  | "--output" :: [] => Except.error "missing path after --output"
  | "-o" :: [] => Except.error "missing path after -o"
  | "--help" :: [] => Except.error usage
  | arg :: _ => Except.error ("unknown argument: " ++ arg)

def main (args : List String) : IO UInt32 := do
  match parseArgs args with
  | Except.error e =>
      IO.eprintln e
      IO.eprintln usage
      pure 2
  | Except.ok output? =>
      try
        let sysroot ← findSysroot
        initSearchPath sysroot
        let imports := trustedRoots.map fun m => { module := m : Import }
        let env ← importModules imports {} 0
        let projFindings := projectAxiomFindings env
        let (declReports, declFindings) := declAxiomReports env
        let files ← collectLeanFiles "MathEvidence"
        let mut srcFindings : List Finding := []
        for path in files do
          let text ← IO.FS.readFile path
          let file := normalizePath path.toString
          srcFindings := srcFindings ++ scanLines file (cleanedLines text) 1
        let findings := projFindings ++ declFindings ++ srcFindings
        let json := reportJson env.header.moduleNames.size declReports findings
        match output? with
        | some output => IO.FS.writeFile output json
        | none => IO.println json
        pure (if findings.isEmpty then 0 else 1)
      catch e =>
        IO.eprintln s!"environment axiom audit failed: {e}"
        IO.eprintln "hint: run via `lake exe mathevidence-axiom-report` after `lake build`"
        pure 3
