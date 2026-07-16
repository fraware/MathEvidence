/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.IR.RationalExpr.Wire

open Lean

/-!
Wire-format decoder for adapter JSON (name-based AST). Converts to indexed
`Expr` given an ordered variable-name list.
-/

inductive DecodeError where
  | json (msg : String)
  | badTag (tag : String)
  | unknownVar (name : String)
  | badNumber (detail : String)
  deriving Repr, Inhabited

def DecodeError.toString : DecodeError → String
  | .json m => m
  | .badTag t => s!"bad tag {t}"
  | .unknownVar n => s!"unknown variable {n}"
  | .badNumber d => s!"bad number: {d}"

instance : ToString DecodeError where
  toString := DecodeError.toString

private def lift (e : Except String α) : Except DecodeError α :=
  match e with
  | .ok a => .ok a
  | .error m => .error (.json m)

def varIndex (names : List String) (name : String) : Except DecodeError Nat :=
  match names.findIdx? (· == name) with
  | some i => .ok i
  | none => .error (.unknownVar name)

private def asInt (j : Json) : Except DecodeError Int := do
  match j.getStr? with
  | .ok s =>
    match s.toInt? with
    | some n => pure n
    | none => throw (.badNumber s)
  | .error _ =>
    -- Wire profile uses decimal strings; reject bare JSON numbers for digests.
    throw (.badNumber "expected decimal string for integer")

private def asNat (j : Json) : Except DecodeError Nat := do
  match j.getStr? with
  | .ok s =>
    match s.toNat? with
    | some n => pure n
    | none => throw (.badNumber s)
  | .error _ =>
    match j.getNum? with
    | .ok n =>
      -- Accept small nat literals for exponents only when encoded as JSON numbers.
      if n.exponent == 0 && n.mantissa ≥ 0 then
        pure n.mantissa.toNat
      else
        throw (.badNumber "non-nat Json number")
    | .error m => throw (.json m)

partial def decodeExpr (names : List String) (j : Json) : Except DecodeError Expr := do
  let tag ← lift (j.getObjValAs? String "tag")
  match tag with
  | "var" =>
    let name ← lift (j.getObjValAs? String "name")
    let i ← varIndex names name
    pure (.var i)
  | "int" =>
    let v ← lift (j.getObjVal? "value")
    let n ← asInt v
    pure (.int n)
  | "rat" =>
    let n ← asInt (← lift (j.getObjVal? "n"))
    let d ← asNat (← lift (j.getObjVal? "d"))
    pure (.rat n d)
  | "neg" =>
    let arg ← match j.getObjVal? "arg" with
      | .ok a => pure a
      | .error _ => lift (j.getObjVal? "e")
    pure (.neg (← decodeExpr names arg))
  | "add" =>
    pure (.add (← decodeExpr names (← lift (j.getObjVal? "left")))
      (← decodeExpr names (← lift (j.getObjVal? "right"))))
  | "sub" =>
    pure (.sub (← decodeExpr names (← lift (j.getObjVal? "left")))
      (← decodeExpr names (← lift (j.getObjVal? "right"))))
  | "mul" =>
    pure (.mul (← decodeExpr names (← lift (j.getObjVal? "left")))
      (← decodeExpr names (← lift (j.getObjVal? "right"))))
  | "pow" =>
    let base ← decodeExpr names (← lift (j.getObjVal? "base"))
    let expJ ← match j.getObjVal? "exp" with
      | .ok e => pure e
      | .error _ => lift (j.getObjVal? "k")
    let k ← asNat expJ
    pure (.pow base k)
  | "div" =>
    pure (.div (← decodeExpr names (← lift (j.getObjVal? "num")))
      (← decodeExpr names (← lift (j.getObjVal? "den"))))
  | other => throw (.badTag other)

/-- Parse a JSON string into an IR expression. -/
def decodeExprString (names : List String) (s : String) : Except DecodeError Expr := do
  let j ← lift (Json.parse s)
  decodeExpr names j

end MathEvidence.IR.RationalExpr.Wire
