/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.IR.RationalExpr

/-- Restricted rational-expression syntax over a field (RFC 0001 / Product 01).

Variables are de Bruijn-style indices into an environment of size `varCount`.
Unsupported Lean constructs (transcendentals, conditionals, approx numerals, …)
never appear as constructors — rejection happens at reification. -/
inductive Expr where
  | var (idx : Nat)
  | int (n : Int)
  /-- Rational literal `n / d` with explicit positive denominator `d`. -/
  | rat (n : Int) (d : Nat)
  | neg (e : Expr)
  | add (a b : Expr)
  | sub (a b : Expr)
  | mul (a b : Expr)
  | pow (base : Expr) (k : Nat)
  | div (num den : Expr)
  deriving DecidableEq, Repr, Inhabited

/-- Structural size measure for resource limits. -/
def Expr.size : Expr → Nat
  | .var _ | .int _ | .rat _ _ => 1
  | .neg e => 1 + e.size
  | .add a b | .sub a b | .mul a b | .div a b => 1 + a.size + b.size
  | .pow b _ => 1 + b.size

/-- Maximum variable index mentioned (exclusive upper bound of needed env). -/
def Expr.maxVarIdx : Expr → Nat
  | .var i => i + 1
  | .int _ | .rat _ _ => 0
  | .neg e => e.maxVarIdx
  | .add a b | .sub a b | .mul a b | .div a b => Nat.max a.maxVarIdx b.maxVarIdx
  | .pow b _ => b.maxVarIdx

/-- True when every `rat` literal has nonzero denominator and vars are `< varCount`. -/
def Expr.wellFormed (varCount : Nat) : Expr → Bool
  | .var i => decide (i < varCount)
  | .int _ => true
  | .rat _ d => decide (d ≠ 0)
  | .neg e => e.wellFormed varCount
  | .add a b | .sub a b | .mul a b | .div a b =>
    a.wellFormed varCount && b.wellFormed varCount
  | .pow b _ => b.wellFormed varCount

/-- Collect denominator subexpressions appearing under `div` (and `rat` dens as ints). -/
def Expr.denominators : Expr → List Expr
  | .var _ | .int _ => []
  | .rat _ d => [.int (Int.ofNat d)]
  | .neg e => e.denominators
  | .add a b | .sub a b | .mul a b => a.denominators ++ b.denominators
  | .pow b _ => b.denominators
  | .div n d => n.denominators ++ d.denominators ++ [d]

/-- Reject if size exceeds a hard cap (resource policy). -/
def Expr.withinSizeLimit (e : Expr) (limit : Nat) : Bool :=
  decide (e.size ≤ limit)

end MathEvidence.IR.RationalExpr
