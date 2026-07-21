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

/-- Terms over finite typed variables (de Bruijn indices into `domains`). -/
inductive Term where
  | var (idx : Nat)
  | lit (v : Val)
  | neg (t : Term)
  | add (a b : Term)
  | sub (a b : Term)
  | mul (a b : Term)
  deriving DecidableEq, Repr, Inhabited

/-- Domain bound for a variable (interpretation depends on `Ty`).

* `bool`: ignored (domain is `{false, true}`)
* `nat`: values `0 .. bound` inclusive when `bound` is `some n`;
  alternatively `lowerBound`/`upperBound` may be terms over earlier binders
* `int`: values `-bound .. bound` inclusive when `bound` is `some n`;
  alternatively `lowerBound`/`upperBound` may be terms over earlier binders
-/
structure Domain where
  ty : Ty
  /-- Inclusive non-dependent bound retained for compact constant domains. -/
  bound : Option Nat := none
  /-- Optional lower bound term over earlier variables; absent means `0` for Nat. -/
  lowerBound : Option Term := none
  /-- Optional upper bound term over earlier variables. -/
  upperBound : Option Term := none
  deriving DecidableEq, Repr, Inhabited

/-- Assignment: one value per domain variable. -/
abbrev Assignment := List Val

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

/-- Domain well-formedness ignoring binder-order dependencies. -/
def Domain.wellFormed : Domain → Bool
  | ⟨.bool, _, _, _⟩ => true
  | ⟨.nat, some _, none, none⟩ => true
  | ⟨.nat, none, _, some _⟩ => true
  | ⟨.int, some _, none, none⟩ => true
  | ⟨.int, none, some _, some _⟩ => true
  | ⟨.nat, _, _, _⟩ | ⟨.int, _, _, _⟩ => false

/-- Terms are well-formed relative to a domain list. -/
def Term.wellFormed (doms : List Domain) : Term → Bool
  | .var i => decide (i < doms.length)
  | .lit _ => true
  | .neg t => t.wellFormed doms
  | .add a b | .sub a b | .mul a b => a.wellFormed doms && b.wellFormed doms

def Domain.boundTermsWellFormed (ctx : List Domain) (d : Domain) : Bool :=
  (match d.lowerBound with
    | none => true
    | some t => t.wellFormed ctx) &&
  (match d.upperBound with
    | none => true
    | some t => t.wellFormed ctx)

def domainsWellFormed : List Domain → Bool
  | [] => true
  | d :: ds =>
    d.wellFormed && d.boundTermsWellFormed [] &&
      let rec go (ctx rest : List Domain) : Bool :=
        match rest with
        | [] => true
        | d :: ds =>
          d.wellFormed && d.boundTermsWellFormed ctx &&
            go (ctx ++ [d]) ds
      go [d] ds

def valToInt : Val → Option Int
  | .nat n => some (Int.ofNat n)
  | .int i => some i
  | .bool _ => none

def evalBoundTerm (σ : Assignment) : Term → Option Val
  | .var i => σ.get? i
  | .lit v => some v
  | .neg t =>
    match evalBoundTerm σ t with
    | some (.int i) => some (.int (-i))
    | some (.nat n) => some (.int (-(Int.ofNat n)))
    | _ => none
  | .add a b =>
    match evalBoundTerm σ a, evalBoundTerm σ b with
    | some (.int x), some (.int y) => some (.int (x + y))
    | some (.nat x), some (.nat y) => some (.nat (x + y))
    | some (.int x), some (.nat y) => some (.int (x + Int.ofNat y))
    | some (.nat x), some (.int y) => some (.int (Int.ofNat x + y))
    | _, _ => none
  | .sub a b =>
    match evalBoundTerm σ a, evalBoundTerm σ b with
    | some (.int x), some (.int y) => some (.int (x - y))
    | some (.nat x), some (.nat y) =>
      if y ≤ x then some (.nat (x - y)) else some (.int (Int.ofNat x - Int.ofNat y))
    | some (.int x), some (.nat y) => some (.int (x - Int.ofNat y))
    | some (.nat x), some (.int y) => some (.int (Int.ofNat x - y))
    | _, _ => none
  | .mul a b =>
    match evalBoundTerm σ a, evalBoundTerm σ b with
    | some (.int x), some (.int y) => some (.int (x * y))
    | some (.nat x), some (.nat y) => some (.nat (x * y))
    | some (.int x), some (.nat y) => some (.int (x * Int.ofNat y))
    | some (.nat x), some (.int y) => some (.int (Int.ofNat x * y))
    | _, _ => none

def evalBoundAsInt (σ : Assignment) (t : Term) : Option Int :=
  match evalBoundTerm σ t with
  | some v => valToInt v
  | none => none

/-- Value inhabits a domain. -/
def Val.inDomain : Val → Domain → Bool
  | .bool _, ⟨.bool, _, _, _⟩ => true
  | .nat n, ⟨.nat, some b, none, none⟩ => decide (n ≤ b)
  | .int i, ⟨.int, some b, none, none⟩ =>
    decide (-(Int.ofNat b) ≤ i ∧ i ≤ Int.ofNat b)
  | _, _ => false

/-- Value inhabits a possibly dependent domain under earlier binder assignments. -/
def Val.inDomainWith (ctx : Assignment) (v : Val) (d : Domain) : Bool :=
  match v, d with
  | .bool _, ⟨.bool, _, _, _⟩ => true
  | .nat n, ⟨.nat, some b, none, none⟩ => decide (n ≤ b)
  | .nat n, ⟨.nat, none, lo?, some hi⟩ =>
    match evalBoundAsInt ctx hi with
    | none => false
    | some upper =>
      let lower :=
        match lo? with
        | none => some 0
        | some lo => evalBoundAsInt ctx lo
      match lower with
      | none => false
      | some lower => decide (lower ≤ Int.ofNat n ∧ Int.ofNat n ≤ upper)
  | .int i, ⟨.int, some b, none, none⟩ =>
    decide (-(Int.ofNat b) ≤ i ∧ i ≤ Int.ofNat b)
  | .int i, ⟨.int, none, some lo, some hi⟩ =>
    match evalBoundAsInt ctx lo, evalBoundAsInt ctx hi with
    | some lower, some upper => decide (lower ≤ i ∧ i ≤ upper)
    | _, _ => false
  | _, _ => false

def Pred.wellFormed (doms : List Domain) : Pred → Bool
  | .eq a b | .ne a b | .le a b | .lt a b =>
    a.wellFormed doms && b.wellFormed doms
  | .not p => p.wellFormed doms
  | .and a b | .or a b => a.wellFormed doms && b.wellFormed doms

def Pred.withinSizeLimit (p : Pred) (limit : Nat := defaultSizeLimit) : Bool :=
  decide (p.size ≤ limit)

def Assignment.wellFormed (doms : List Domain) (σ : Assignment) : Bool :=
  let rec go (ctx : Assignment) (doms : List Domain) (σ : Assignment) : Bool :=
    match doms, σ with
    | [], [] => true
    | d :: ds, v :: vs =>
      v.inDomainWith ctx d && go (ctx ++ [v]) ds vs
    | _, _ => false
  domainsWellFormed doms && go [] doms σ

end MathEvidence.IR.FinitePredicate
