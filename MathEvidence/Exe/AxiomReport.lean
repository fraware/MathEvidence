import Std

/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/

/-!
# `mathevidence-axiom-report`

Compiled Lake driver for the PR trust audit gate. This pass walks committed Lean
sources and performs a labeled source scan for `sorry`/`admit`/`sorryAx`, project
`axiom` declarations, and unauthorized `unsafe` usage in trusted packages.

This is intentionally reported as a compiled driver plus source scan. It is not
yet a Lean environment audit over imported constants and transitive axioms.
-/

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

def reportJson (filesScanned : Nat) (findings : List Finding) : String :=
  "{" ++ joinWith "," [
    "\"tool\":\"mathevidence-axiom-report\"",
    "\"status\":" ++ jsonString (if findings.isEmpty then "pass" else "fail"),
    "\"scanMode\":\"compiled Lean driver + source scan\"",
    "\"authority\":\"authoritative Lake executable for this gate when available; source-pattern scan until a true Lean environment audit exists\"",
    "\"scanRoot\":\"MathEvidence\"",
    "\"filesScanned\":" ++ toString filesScanned,
    "\"policy\":{\"failOn\":[\"sorryAx\",\"sorry\",\"admit\",\"project_axiom\",\"unauthorized_unsafe_in_Core_IR_Encoding_Checkers\"]}",
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
      let files ← collectLeanFiles "MathEvidence"
      let mut findings : List Finding := []
      for path in files do
        let text ← IO.FS.readFile path
        let file := normalizePath path.toString
        findings := findings ++ scanLines file (cleanedLines text) 1
      let json := reportJson files.length findings
      match output? with
      | some output => IO.FS.writeFile output json
      | none => IO.println json
      pure (if findings.isEmpty then 0 else 1)
