/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.IR.FinitePredicate

/-- Supported finite scalar types for witnesses. -/
inductive Ty where
  | bool
  | nat
  | int
  deriving DecidableEq, Repr, Inhabited

/-- Typed finite value. -/
inductive Val where
  | bool (b : Bool)
  | nat (n : Nat)
  | int (i : Int)
  deriving DecidableEq, Repr, Inhabited

/-- Domain bound for a variable (interpretation depends on `Ty`).

* `bool`: ignored (domain is `{false, true}`)
* `nat`: values `0 .. bound` inclusive when `bound` is `some n`; unbounded rejected
* `int`: values `-bound .. bound` inclusive when `bound` is `some n`
-/
structure Domain where
  ty : Ty
  /-- Inclusive bound for `nat`/`int` domains; required for well-formedness. -/
  bound : Option Nat := none
  deriving DecidableEq, Repr, Inhabited

/-- Terms over finite typed variables (de Bruijn indices into `domains`). -/
inductive Term where
  | var (idx : Nat)
  | lit (v : Val)
  | neg (t : Term)
  | add (a b : Term)
  | sub (a b : Term)
  | mul (a b : Term)
  deriving DecidableEq, Repr, Inhabited

/-- Boolean predicates over finite terms.

Universal / existential quantification over finite domains is expressible, but
**exhaustive absence** of counterexamples is outside the Counterexample checker. -/
inductive Pred where
  | eq (a b : Term)
  | ne (a b : Term)
  | le (a b : Term)
  | lt (a b : Term)
  | not (p : Pred)
  | and (a b : Pred)
  | or (a b : Pred)
  deriving DecidableEq, Repr, Inhabited

/-- Structural size. -/
def Term.size : Term → Nat
  | .var _ | .lit _ => 1
  | .neg t => 1 + t.size
  | .add a b | .sub a b | .mul a b => 1 + a.size + b.size

def Pred.size : Pred → Nat
  | .eq a b | .ne a b | .le a b | .lt a b => 1 + a.size + b.size
  | .not p => 1 + p.size
  | .and a b | .or a b => 1 + a.size + b.size

def Term.maxVarIdx : Term → Nat
  | .var i => i + 1
  | .lit _ => 0
  | .neg t => t.maxVarIdx
  | .add a b | .sub a b | .mul a b => Nat.max a.maxVarIdx b.maxVarIdx

def Pred.maxVarIdx : Pred → Nat
  | .eq a b | .ne a b | .le a b | .lt a b => Nat.max a.maxVarIdx b.maxVarIdx
  | .not p => p.maxVarIdx
  | .and a b | .or a b => Nat.max a.maxVarIdx b.maxVarIdx

def defaultSizeLimit : Nat := 10000

/-- Domain well-formedness: `nat`/`int` require an explicit bound. -/
def Domain.wellFormed : Domain → Bool
  | ⟨.bool, _⟩ => true
  | ⟨.nat, some _⟩ => true
  | ⟨.int, some _⟩ => true
  | ⟨.nat, none⟩ | ⟨.int, none⟩ => false

/-- Value inhabits a domain. -/
def Val.inDomain : Val → Domain → Bool
  | .bool _, ⟨.bool, _⟩ => true
  | .nat n, ⟨.nat, some b⟩ => decide (n ≤ b)
  | .int i, ⟨.int, some b⟩ =>
    decide (-(Int.ofNat b) ≤ i ∧ i ≤ Int.ofNat b)
  | _, _ => false

/-- Terms are well-formed relative to a domain list. -/
def Term.wellFormed (doms : List Domain) : Term → Bool
  | .var i => decide (i < doms.length)
  | .lit _ => true
  | .neg t => t.wellFormed doms
  | .add a b | .sub a b | .mul a b => a.wellFormed doms && b.wellFormed doms

def Pred.wellFormed (doms : List Domain) : Pred → Bool
  | .eq a b | .ne a b | .le a b | .lt a b =>
    a.wellFormed doms && b.wellFormed doms
  | .not p => p.wellFormed doms
  | .and a b | .or a b => a.wellFormed doms && b.wellFormed doms

def Pred.withinSizeLimit (p : Pred) (limit : Nat := defaultSizeLimit) : Bool :=
  decide (p.size ≤ limit)

/-- Assignment: one value per domain variable. -/
abbrev Assignment := List Val

def Assignment.wellFormed (doms : List Domain) (σ : Assignment) : Bool :=
  decide (σ.length = doms.length) &&
    (List.zip σ doms).all fun p => p.1.inDomain p.2

end MathEvidence.IR.FinitePredicate
