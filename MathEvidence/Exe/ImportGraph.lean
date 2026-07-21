import Std

/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/

/-!
# `mathevidence-import-graph`

Compiled Lake driver for trusted-package import boundary checks. It walks
`MathEvidence/Core`, `MathEvidence/IR`, `MathEvidence/Encoding` when present,
and `MathEvidence/Checkers`, parses Lean `import` lines, and emits a JSON
allowlist/denylist report.
-/

structure Violation where
  file : String
  line : Nat
  kind : String
  moduleOrPattern : String
  reason : String
  deriving Repr

def usage : String :=
  "usage: mathevidence-import-graph [--output <path>]"

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
    try
      dir.readDir
    catch _ =>
      pure #[]
  let mut files : List System.FilePath := []
  for entry in entries do
    if ← entry.path.isDir then
      files := files ++ (← collectLeanFiles entry.path)
    else if isLeanFile entry.path then
      files := files ++ [entry.path]
  pure files

def trustedRootFiles : List System.FilePath :=
  ["MathEvidence/Core.lean", "MathEvidence/IR.lean", "MathEvidence/Encoding.lean", "MathEvidence/Checkers.lean"]

def trustedDirs : List System.FilePath :=
  ["MathEvidence/Core", "MathEvidence/IR", "MathEvidence/Encoding", "MathEvidence/Checkers"]

def existingFile? (path : System.FilePath) : IO (Option System.FilePath) := do
  let pathExists ← path.pathExists
  pure (if pathExists then some path else none)

def collectTrustedFiles : IO (List System.FilePath) := do
  let mut files : List System.FilePath := []
  for dir in trustedDirs do
    files := files ++ (← collectLeanFiles dir)
  for file in trustedRootFiles do
    let file? ← existingFile? file
    match file? with
    | some path => files := files ++ [path]
    | none => pure ()
  pure files

def isForbiddenModule (moduleName : String) : Option String :=
  if moduleName == "MathEvidence.Tactic" || moduleName.startsWith "MathEvidence.Tactic." then
    some "trusted packages must not import tactic-facing code"
  else if moduleName == "IO" || moduleName.startsWith "IO." || containsSubstr moduleName ".IO." then
    some "trusted packages must not import IO-facing modules"
  else if moduleName == "MathEvidence.Agent" || moduleName.startsWith "MathEvidence.Agent." || moduleName == "Agent" || moduleName.startsWith "Agent." then
    some "trusted packages must not import agent orchestration"
  else if moduleName == "adapters" || moduleName.startsWith "adapters." || moduleName == "Adapters" || moduleName.startsWith "Adapters." || moduleName == "MathEvidence.Adapters" || moduleName.startsWith "MathEvidence.Adapters." then
    some "trusted packages must not import adapters"
  else if moduleName == "Network" || moduleName.startsWith "Network." || moduleName == "MathEvidence.Network" || moduleName.startsWith "MathEvidence.Network." then
    some "trusted packages must not import network modules"
  else if moduleName == "Process" || moduleName.startsWith "Process." || moduleName == "MathEvidence.Process" || moduleName.startsWith "MathEvidence.Process." then
    some "trusted packages must not import process modules"
  else if moduleName == "Studio" || moduleName.startsWith "Studio." || moduleName == "MathEvidence.Studio" || moduleName.startsWith "MathEvidence.Studio." then
    some "trusted packages must not import Studio"
  else if moduleName == "Foundry" || moduleName.startsWith "Foundry." || moduleName == "MathEvidence.Foundry" || moduleName.startsWith "MathEvidence.Foundry." then
    some "trusted packages must not import Foundry"
  else
    none

def forbiddenReferencePatterns : List (String × String) :=
  [
    ("IO.Process", "trusted packages must not invoke process APIs"),
    ("Network.", "trusted packages must not reference network APIs"),
    ("Socket.", "trusted packages must not reference socket APIs"),
    ("adapters.", "trusted packages must not reference adapters")
  ]

def importModulesFromLine (line : String) : List String :=
  let trimmed := line.trim
  if trimmed.startsWith "import " then
    (trimmed.drop "import ".length).splitOn " " |>.filter (fun part => !part.trim.isEmpty)
  else
    []

def scanLine (file : String) (lineNumber : Nat) (line : String) : List Violation :=
  let importViolations :=
    (importModulesFromLine line).filterMap fun moduleName =>
      match isForbiddenModule moduleName with
      | some reason =>
        some {
          file,
          line := lineNumber,
          kind := "forbidden_import",
          moduleOrPattern := moduleName,
          reason
        }
      | none => none
  let referenceViolations :=
    forbiddenReferencePatterns.filterMap fun (pattern, reason) =>
      if containsSubstr line pattern then
        some {
          file,
          line := lineNumber,
          kind := "forbidden_reference",
          moduleOrPattern := pattern,
          reason
        }
      else
        none
  importViolations ++ referenceViolations

partial def scanLines (file : String) : List String → Nat → List Violation
  | [], _ => []
  | line :: rest, lineNumber =>
      scanLine file lineNumber line ++ scanLines file rest (lineNumber + 1)

def violationJson (violation : Violation) : String :=
  "{" ++ joinWith "," [
    "\"file\":" ++ jsonString violation.file,
    "\"line\":" ++ toString violation.line,
    "\"kind\":" ++ jsonString violation.kind,
    "\"moduleOrPattern\":" ++ jsonString violation.moduleOrPattern,
    "\"reason\":" ++ jsonString violation.reason
  ] ++ "}"

def reportJson (filesScanned : Nat) (violations : List Violation) : String :=
  "{" ++ joinWith "," [
    "\"tool\":\"mathevidence-import-graph\"",
    "\"status\":" ++ jsonString (if violations.isEmpty then "pass" else "fail"),
    "\"scanMode\":\"compiled Lean driver + import/source-boundary scan\"",
    "\"scanRoots\":[\"MathEvidence/Core\",\"MathEvidence/IR\",\"MathEvidence/Encoding\",\"MathEvidence/Checkers\"]",
    "\"allowlist\":{\"trustedPackages\":[\"Core\",\"IR\",\"Encoding\",\"Checkers\"],\"allowedImports\":\"Lean/Std/Mathlib and MathEvidence trusted layers unless denied below\"}",
    "\"denylist\":[\"MathEvidence.Tactic\",\"IO\",\"Agent\",\"adapters\",\"Network\",\"Process\",\"Studio\",\"Foundry\",\"IO.Process\",\"Socket\" ]",
    "\"filesScanned\":" ++ toString filesScanned,
    "\"violations\":[" ++ joinWith "," (violations.map violationJson) ++ "]"
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
      let files ← collectTrustedFiles
      let mut violations : List Violation := []
      for path in files do
        let text ← IO.FS.readFile path
        let file := normalizePath path.toString
        violations := violations ++ scanLines file (cleanedLines text) 1
      let json := reportJson files.length violations
      match output? with
      | some output => IO.FS.writeFile output json
      | none => IO.println json
      pure (if violations.isEmpty then 0 else 1)
