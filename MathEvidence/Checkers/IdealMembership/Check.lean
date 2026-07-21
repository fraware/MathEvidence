/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.Polynomial.Basic
import Mathlib.RingTheory.Ideal.Basic
import Mathlib.RingTheory.Ideal.Span
import MathEvidence.IR.Polynomial.Syntax

/-!
# Ideal membership checker

Claim class: membership only. Certificate is coefficient witnesses `qᵢ` such that
`f = Σ qᵢ · gᵢ` in the sparse polynomial IR (after like-term normalization).
Non-membership / radical / Gröbner correctness are out of scope.

## Mathlib-facing theorem shape (documented + coded)

Federation target (auto-bridge for univariate and `MvPolynomial (Fin n)` spans):

```lean
theorem membership_from_witness_univariate
    {R : Type*} [CommRing R]
    (f g q : R[X]) (h : f = q * g) :
    f ∈ Ideal.span {g}

theorem membership_from_witness_pair
    {R : Type*} [CommRing R]
    (f g₁ g₂ q₁ q₂ : R) (h : f = q₁ * g₁ + q₂ * g₂) :
    f ∈ Ideal.span {g₁, g₂}
```

`mathevidence_ideal_membership` reifies concrete `f ∈ Ideal.span {g}` /
`f ∈ Ideal.span {g₁, g₂}` goals over univariate `ℤ[X]` / `ℚ[X]` or
`MvPolynomial (Fin n) ℤ` / `ℚ` (reify `2≤n≤4`; Meta close for `n=2,3`), proposes a
sparse witness (exact univariate / grevlex mv division, incl. non-monomial gens
when an exact ℤ quotient exists), gates on `checkMembership`, then closes via the
theorems above + `ring`.
-/

namespace MathEvidence.Checkers.IdealMembership

open MathEvidence.IR.Polynomial
open Polynomial

/-- Combine like terms (same monomial exponents); drop zero coefficients. -/
def normalize (p : SparsePoly) : SparsePoly :=
  Id.run do
    let mut acc : List Term := []
    for t in p.terms do
      if t.coefficient == 0 then continue
      let mut found := false
      let mut next : List Term := []
      for u in acc do
        if u.monomial.exponents == t.monomial.exponents then
          let c := u.coefficient + t.coefficient
          found := true
          if c != 0 then
            next := next ++ [{ coefficient := c, monomial := u.monomial }]
        else
          next := next ++ [u]
      if !found then
        next := next ++ [t]
      acc := next
    -- Insertion-sort by exponents for stable structural equality.
    let mut sorted : List Term := []
    for t in acc do
      let mut placed := false
      let mut out : List Term := []
      for u in sorted do
        if !placed && decide (t.monomial.exponents ≤ u.monomial.exponents) then
          out := out ++ [t, u]
          placed := true
        else
          out := out ++ [u]
      if !placed then out := out ++ [t]
      sorted := out
    pure { varCount := p.varCount, terms := sorted }

/-- Reject reasons for the ideal-membership Boolean gate. -/
inductive RejectReason where
  | lengthMismatch
  | identityFailed
  deriving DecidableEq, Repr, Inhabited

/-- Structured check result (clear accept / reject paths). -/
inductive CheckResult where
  | accept
  | reject (reason : RejectReason)
  deriving DecidableEq, Repr, Inhabited

/-- Boolean certificate check: reconstruct linear combination equality. -/
def checkMembership (f : SparsePoly) (gens : List SparsePoly) (coeffs : List SparsePoly) : Bool :=
  gens.length == coeffs.length &&
    let combo :=
      (List.zip gens coeffs).foldl (init := SparsePoly.zero f.varCount) fun acc pair =>
        SparsePoly.add acc (SparsePoly.mul pair.2 pair.1)
    normalize combo == normalize f

/-- Structured check with explicit reject reasons. -/
def checkMembershipDetailed
    (f : SparsePoly) (gens : List SparsePoly) (coeffs : List SparsePoly) : CheckResult :=
  if gens.length != coeffs.length then
    .reject .lengthMismatch
  else
    let combo :=
      (List.zip gens coeffs).foldl (init := SparsePoly.zero f.varCount) fun acc pair =>
        SparsePoly.add acc (SparsePoly.mul pair.2 pair.1)
    if normalize combo == normalize f then
      .accept
    else
      .reject .identityFailed

/-- Concrete witness acceptance package. -/
structure MembershipWitness where
  target : SparsePoly
  generators : List SparsePoly
  multipliers : List SparsePoly
  deriving DecidableEq, Repr, Inhabited

def MembershipWitness.check (w : MembershipWitness) : Bool :=
  checkMembership w.target w.generators w.multipliers

def MembershipWitness.checkDetailed (w : MembershipWitness) : CheckResult :=
  checkMembershipDetailed w.target w.generators w.multipliers

/-- Example: `xy ∈ ⟨x, y⟩` via multipliers `(y, 0)`. -/
def example_xy : MembershipWitness where
  target := {
    varCount := 2
    terms := [{ coefficient := 1, monomial := ⟨[1, 1]⟩ }]
  }
  generators := [
    { varCount := 2, terms := [{ coefficient := 1, monomial := ⟨[1, 0]⟩ }] },
    { varCount := 2, terms := [{ coefficient := 1, monomial := ⟨[0, 1]⟩ }] }
  ]
  multipliers := [
    { varCount := 2, terms := [{ coefficient := 1, monomial := ⟨[0, 1]⟩ }] },
    SparsePoly.zero 2
  ]

theorem example_xy_accepts : example_xy.check = true := by native_decide

theorem example_xy_detailed_accepts :
    example_xy.checkDetailed = .accept := by native_decide

/-- Example: `x² - 1 ∈ ⟨x - 1⟩` with multiplier `x + 1`. -/
def example_x2_minus_1 : MembershipWitness where
  target := {
    varCount := 1
    terms := [
      { coefficient := 1, monomial := ⟨[2]⟩ },
      { coefficient := -1, monomial := ⟨[0]⟩ }
    ]
  }
  generators := [
    { varCount := 1, terms := [
        { coefficient := 1, monomial := ⟨[1]⟩ },
        { coefficient := -1, monomial := ⟨[0]⟩ }
      ] }
  ]
  multipliers := [
    { varCount := 1, terms := [
        { coefficient := 1, monomial := ⟨[1]⟩ },
        { coefficient := 1, monomial := ⟨[0]⟩ }
      ] }
  ]

theorem example_x2_minus_1_accepts : example_x2_minus_1.check = true := by native_decide

/-- Reject path: length mismatch. -/
theorem reject_length_mismatch :
    checkMembershipDetailed
      example_xy.target example_xy.generators [] = .reject .lengthMismatch := by
  native_decide

/-- Reject path: wrong multipliers fail the normalized identity. -/
theorem reject_identity_failed :
    checkMembershipDetailed
      example_x2_minus_1.target
      example_x2_minus_1.generators
      [SparsePoly.zero 1] = .reject .identityFailed := by
  native_decide

/-- Leading term of a univariate sparse polynomial (max degree; none if zero). -/
def leadingUnivariate? (p : SparsePoly) : Option (Int × Nat) :=
  Id.run do
    let mut best : Option (Int × Nat) := none
    for t in normalize p |>.terms do
      let e := t.monomial.exponents.getD 0 0
      match best with
      | none => best := some (t.coefficient, e)
      | some (_, be) =>
        if e > be then best := some (t.coefficient, e)
    pure best

/-- Exact univariate division over ℤ: return `q` when `normalize (q * g) = normalize f`. -/
def exactQuotientUnivariate? (f g : SparsePoly) : Option SparsePoly :=
  if f.varCount != 1 || g.varCount != 1 then none
  else
    match leadingUnivariate? g with
    | none => none
    | some (lcG, degG) =>
      if lcG == 0 then none
      else
        Id.run do
          let mut rem := normalize f
          let mut qTerms : List Term := []
          let mut guard := (normalize f).terms.length + 8
          while guard > 0 do
            guard := guard - 1
            match leadingUnivariate? rem with
            | none =>
              return some (normalize { varCount := 1, terms := qTerms })
            | some (lcR, degR) =>
              if degR < degG then
                return none
              if lcR % lcG != 0 then
                return none
              let c := lcR / lcG
              let e := degR - degG
              let mon : Term := { coefficient := c, monomial := ⟨[e]⟩ }
              qTerms := qTerms ++ [mon]
              let step := SparsePoly.mul { varCount := 1, terms := [mon] } g
              -- rem := rem - step (negate coefficients of step then add)
              let negStep : SparsePoly := {
                varCount := 1
                terms := step.terms.map fun t =>
                  { t with coefficient := -t.coefficient }
              }
              rem := normalize (SparsePoly.add rem negStep)
          pure none

/-- Constant univariate `c ∈ ℤ[X]`. -/
def constUnivariate (c : Int) : SparsePoly :=
  if c == 0 then SparsePoly.zero 1
  else { varCount := 1, terms := [{ coefficient := c, monomial := ⟨[0]⟩ }] }

/-- Monomial univariate `c · X^e`. -/
def monomialUnivariate (c : Int) (e : Nat) : SparsePoly :=
  if c == 0 then SparsePoly.zero 1
  else { varCount := 1, terms := [{ coefficient := c, monomial := ⟨[e]⟩ }] }

/-- Sparse subtraction via coefficient negation. -/
def sparseSub (a b : SparsePoly) : SparsePoly :=
  let negB : SparsePoly := {
    varCount := b.varCount
    terms := b.terms.map fun t => { t with coefficient := -t.coefficient }
  }
  normalize (SparsePoly.add a negB)

/-- Propose `(q₁, q₂)` for univariate `f = q₁·g₁ + q₂·g₂` (exact-division + small search). -/
def proposePairWitnessUnivariate? (f g₁ g₂ : SparsePoly) :
    Option (SparsePoly × SparsePoly) :=
  if f.varCount != 1 || g₁.varCount != 1 || g₂.varCount != 1 then none
  else
    Id.run do
      let mut found : Option (SparsePoly × SparsePoly) := none
      -- Principal paths: one multiplier absorbs `f`.
      match exactQuotientUnivariate? f g₁ with
      | some q =>
        if checkMembership f [g₁, g₂] [q, SparsePoly.zero 1] then
          found := some (normalize q, SparsePoly.zero 1)
      | none => pure ()
      if found.isNone then
        match exactQuotientUnivariate? f g₂ with
        | some q =>
          if checkMembership f [g₁, g₂] [SparsePoly.zero 1, q] then
            found := some (SparsePoly.zero 1, normalize q)
        | none => pure ()
      -- Small monomial search: q = c·X^e, then exact-divide residual by the other generator.
      if found.isNone then
        for e in List.range 4 do
          for c in [(-8 : Int), -4, -2, -1, 1, 2, 3, 4, 8] do
            if found.isSome then break
            let q1 := monomialUnivariate c e
            let rem := sparseSub f (SparsePoly.mul q1 g₁)
            match exactQuotientUnivariate? rem g₂ with
            | some q2 =>
              if checkMembership f [g₁, g₂] [q1, q2] then
                found := some (normalize q1, normalize q2)
            | none => pure ()
            if found.isSome then break
            let q2 := monomialUnivariate c e
            let rem₂ := sparseSub f (SparsePoly.mul q2 g₂)
            match exactQuotientUnivariate? rem₂ g₁ with
            | some q1' =>
              if checkMembership f [g₁, g₂] [q1', q2] then
                found := some (normalize q1', normalize q2)
            | none => pure ()
      pure found

/-- Recognize a single-term (monomial) sparse polynomial. -/
def asMonomial? (p : SparsePoly) : Option (Int × List Nat) :=
  match (normalize p).terms with
  | [t] => some (t.coefficient, t.monomial.exponents)
  | _ => none

/-- Componentwise `a ≤ b` on equal-length exponent lists. -/
def expsLe (a b : List Nat) : Bool :=
  a.length == b.length &&
    (List.zip a b).all fun p => decide (p.1 ≤ p.2)

/-- Componentwise subtraction of exponent lists (precondition: `expsLe a b`). -/
def expsSub (a b : List Nat) : List Nat :=
  (List.zip b a).map fun p => p.1 - p.2

/-- Exact division of `f` by a single monomial generator over ℤ. -/
def exactQuotientByMonomial? (f g : SparsePoly) : Option SparsePoly :=
  if f.varCount != g.varCount then none
  else
    match asMonomial? g with
    | none => none
    | some (lcG, expG) =>
      if lcG == 0 then none
      else
        Id.run do
          let mut qTerms : List Term := []
          for t in (normalize f).terms do
            let expF := t.monomial.exponents
            if !expsLe expG expF then return none
            if t.coefficient % lcG != 0 then return none
            let c := t.coefficient / lcG
            let e := expsSub expG expF
            if c != 0 then
              qTerms := qTerms ++ [{ coefficient := c, monomial := ⟨e⟩ }]
          let q := normalize { varCount := f.varCount, terms := qTerms }
          if checkMembership f [g] [q] then some q else none

/-- Total degree of an exponent vector. -/
def expsTotalDeg (exps : List Nat) : Nat :=
  exps.foldl (init := 0) (· + ·)

/-- Graded reverse lexicographic comparison: `true` when `a` is strictly greater than `b`.

Higher total degree wins; ties break by reverse lexicographic order (rightmost
differing exponent: smaller exponent is larger in grevlex). -/
def expsGrevlexGt (a b : List Nat) : Bool :=
  if a.length != b.length then false
  else
    let da := expsTotalDeg a
    let db := expsTotalDeg b
    if da != db then decide (da > db)
    else
      Id.run do
        let mut i := a.length
        while i > 0 do
          i := i - 1
          let ai := a.getD i 0
          let bi := b.getD i 0
          if ai != bi then return decide (ai < bi)
        pure false

/-- Leading term of a (possibly multivariate) sparse polynomial under grevlex. -/
def leadingTermMv? (p : SparsePoly) : Option Term :=
  Id.run do
    let mut best : Option Term := none
    for t in normalize p |>.terms do
      match best with
      | none => best := some t
      | some u =>
        if expsGrevlexGt t.monomial.exponents u.monomial.exponents then
          best := some t
    pure best

/-- Exact multivariate division over ℤ: return `q` when `normalize (q * g) = normalize f`.

Uses grevlex leading-term reduction. Prefers the monomial fast path when `g` is
a single term. Supported shapes: principal ideals where `f` is an exact multiple
of `g` in `ℤ[X₀,…,Xₙ₋₁]` with integer coefficient division at each step.
Does not claim Gröbner completeness or non-membership. -/
def exactQuotientMv? (f g : SparsePoly) : Option SparsePoly :=
  if f.varCount != g.varCount || f.varCount < 2 then none
  else
    match asMonomial? g with
    | some _ => exactQuotientByMonomial? f g
    | none =>
      match leadingTermMv? g with
      | none => none
      | some ltG =>
        if ltG.coefficient == 0 then none
        else
          Id.run do
            let n := f.varCount
            let mut rem := normalize f
            let mut qTerms : List Term := []
            -- Bound steps by term count growth under exact division.
            let mut guard := (normalize f).terms.length + (normalize g).terms.length + 16
            while guard > 0 do
              guard := guard - 1
              match leadingTermMv? rem with
              | none =>
                let q := normalize { varCount := n, terms := qTerms }
                if checkMembership f [g] [q] then return some q else return none
              | some ltR =>
                let expG := ltG.monomial.exponents
                let expR := ltR.monomial.exponents
                if !expsLe expG expR then return none
                if ltR.coefficient % ltG.coefficient != 0 then return none
                let c := ltR.coefficient / ltG.coefficient
                let e := expsSub expG expR
                let mon : Term := { coefficient := c, monomial := ⟨e⟩ }
                qTerms := qTerms ++ [mon]
                let step := SparsePoly.mul { varCount := n, terms := [mon] } g
                rem := sparseSub rem step
            pure none

/-- Constant multivariate `c` with `varCount = n`. -/
def constMv (n : Nat) (c : Int) : SparsePoly :=
  if c == 0 then SparsePoly.zero n
  else { varCount := n, terms := [{ coefficient := c, monomial := ⟨List.replicate n 0⟩ }] }

/-- Single-variable monomial `c · X_i^e` in `n` variables. -/
def monomialMv (n i e : Nat) (c : Int) : SparsePoly :=
  if c == 0 || i ≥ n then SparsePoly.zero n
  else
    let exps := (List.range n).map fun j => if j == i then e else 0
    { varCount := n, terms := [{ coefficient := c, monomial := ⟨exps⟩ }] }

/-- Exact singleton quotient: monomial path, else grevlex multivariate division. -/
def exactQuotientSparse? (f g : SparsePoly) : Option SparsePoly :=
  if f.varCount != g.varCount then none
  else if f.varCount == 1 then exactQuotientUnivariate? f g
  else exactQuotientMv? f g

/-- Propose `(q₁, q₂)` for multivariate `f = q₁·g₁ + q₂·g₂`
(exact mv/monomial division + small search). -/
def proposePairWitnessMv? (f g₁ g₂ : SparsePoly) : Option (SparsePoly × SparsePoly) :=
  let n := f.varCount
  if n < 2 || g₁.varCount != n || g₂.varCount != n then none
  else
    Id.run do
      let mut found : Option (SparsePoly × SparsePoly) := none
      match exactQuotientSparse? f g₁ with
      | some q =>
        if checkMembership f [g₁, g₂] [q, SparsePoly.zero n] then
          found := some (normalize q, SparsePoly.zero n)
      | none => pure ()
      if found.isNone then
        match exactQuotientSparse? f g₂ with
        | some q =>
          if checkMembership f [g₁, g₂] [SparsePoly.zero n, q] then
            found := some (SparsePoly.zero n, normalize q)
        | none => pure ()
      -- Small single-variable monomial search then exact-divide residual.
      if found.isNone then
        for i in List.range n do
          for e in List.range 3 do
            for c in [(-4 : Int), -2, -1, 1, 2, 4] do
              if found.isSome then break
              let q1 := monomialMv n i e c
              let rem := sparseSub f (SparsePoly.mul q1 g₁)
              match exactQuotientSparse? rem g₂ with
              | some q2 =>
                if checkMembership f [g₁, g₂] [q1, q2] then
                  found := some (normalize q1, normalize q2)
              | none => pure ()
              if found.isSome then break
              let q2 := monomialMv n i e c
              let rem₂ := sparseSub f (SparsePoly.mul q2 g₂)
              match exactQuotientSparse? rem₂ g₁ with
              | some q1' =>
                if checkMembership f [g₁, g₂] [q1', q2] then
                  found := some (normalize q1', normalize q2)
              | none => pure ()
      pure found

/-- Dispatch pair witness search by arity. -/
def proposePairWitness? (f g₁ g₂ : SparsePoly) : Option (SparsePoly × SparsePoly) :=
  if f.varCount == 1 then proposePairWitnessUnivariate? f g₁ g₂
  else proposePairWitnessMv? f g₁ g₂

/-- Singleton witness: univariate / multivariate exact division (incl. non-monomial gens). -/
def proposeSingletonWitness? (f g : SparsePoly) : Option SparsePoly :=
  exactQuotientSparse? f g

/-- Mathlib-facing shape: witness identity implies ideal membership (univariate). -/
theorem membership_from_witness_univariate
    {R : Type*} [CommRing R]
    (f : R[X]) (g q : R[X]) (h : f = q * g) :
    f ∈ Ideal.span {g} := by
  rw [h]
  exact Ideal.mul_mem_left _ _ (Ideal.subset_span (Set.mem_singleton g))

/-- Two-generator witness identity implies span membership (any CommRing, incl. `R[X]` / MvPolynomial). -/
theorem membership_from_witness_pair
    {R : Type*} [CommRing R]
    (f g₁ g₂ q₁ q₂ : R) (h : f = q₁ * g₁ + q₂ * g₂) :
    f ∈ Ideal.span {g₁, g₂} := by
  rw [h]
  exact Ideal.add_mem _
    (Ideal.mul_mem_left _ _ (Ideal.subset_span (by simp)))
    (Ideal.mul_mem_left _ _ (Ideal.subset_span (by simp)))

/-- Ordinary Mathlib theorem matching the IR `x²−1 ∈ ⟨x−1⟩` certificate shape. -/
theorem mathlib_x2_minus_1_in_span :
    ((X : ℤ[X]) ^ 2 - 1) ∈ Ideal.span {(X : ℤ[X]) - 1} := by
  have h : (X : ℤ[X]) ^ 2 - 1 = (X + 1) * (X - 1) := by
    ring
  exact membership_from_witness_univariate _ _ _ h

/-- Ordinary two-generator Mathlib theorem: `2X ∈ ⟨X+1, X−1⟩`. -/
theorem mathlib_two_x_in_span_pair :
    (2 * (X : ℤ[X])) ∈ Ideal.span {(X : ℤ[X]) + 1, (X : ℤ[X]) - 1} := by
  have h : (2 * (X : ℤ[X])) = (1 : ℤ[X]) * (X + 1) + (1 : ℤ[X]) * (X - 1) := by
    ring
  exact membership_from_witness_pair _ _ _ _ _ h

/-- IR exact-division recovers the classical multiplier for `x²−1 = (x+1)(x−1)`. -/
theorem exact_quotient_x2_minus_1 :
    exactQuotientUnivariate? example_x2_minus_1.target
        (example_x2_minus_1.generators.head!) =
      some (normalize (example_x2_minus_1.multipliers.head!)) := by
  native_decide

/-- Pair witness search recovers `2X = 1·(X+1) + 1·(X−1)`. -/
theorem propose_pair_two_x :
    proposePairWitnessUnivariate?
        { varCount := 1, terms := [{ coefficient := 2, monomial := ⟨[1]⟩ }] }
        { varCount := 1, terms := [
            { coefficient := 1, monomial := ⟨[1]⟩ },
            { coefficient := 1, monomial := ⟨[0]⟩ }] }
        { varCount := 1, terms := [
            { coefficient := 1, monomial := ⟨[1]⟩ },
            { coefficient := -1, monomial := ⟨[0]⟩ }] } =
      some (constUnivariate 1, constUnivariate 1) := by
  native_decide

/-- Adversarial: wrong multipliers fail identity (univariate principal). -/
theorem reject_wrong_witness_x2 :
    checkMembershipDetailed
      example_x2_minus_1.target
      example_x2_minus_1.generators
      [constUnivariate 1] = .reject .identityFailed := by
  native_decide

/-- Adversarial: swapped multipliers for asymmetric two-generator combination. -/
theorem reject_wrong_generator_order_2x_3 :
    checkMembershipDetailed
      { varCount := 1, terms := [
          { coefficient := 2, monomial := ⟨[1]⟩ },
          { coefficient := 3, monomial := ⟨[0]⟩ }] }
      [
        { varCount := 1, terms := [{ coefficient := 1, monomial := ⟨[1]⟩ }] },
        constUnivariate 1
      ]
      -- Correct would be (2, 3); swapped (3, 2) must reject.
      [constUnivariate 3, constUnivariate 2] = .reject .identityFailed := by
  native_decide

/-- Correct order for the same claim accepts. -/
theorem accept_correct_order_2x_3 :
    checkMembership
      { varCount := 1, terms := [
          { coefficient := 2, monomial := ⟨[1]⟩ },
          { coefficient := 3, monomial := ⟨[0]⟩ }] }
      [
        { varCount := 1, terms := [{ coefficient := 1, monomial := ⟨[1]⟩ }] },
        constUnivariate 1
      ]
      [constUnivariate 2, constUnivariate 3] = true := by
  native_decide

/-- Multivariate monomial division recovers `xy = y·x` for `xy ∈ ⟨x,y⟩`. -/
theorem exact_quotient_xy_by_x :
    exactQuotientByMonomial? example_xy.target (example_xy.generators.head!) =
      some (normalize (example_xy.multipliers.head!)) := by
  native_decide

/-- Pair witness search recovers multivariate `xy ∈ ⟨x,y⟩`. -/
theorem propose_pair_xy :
    proposePairWitnessMv? example_xy.target
        (example_xy.generators.get! 0) (example_xy.generators.get! 1) =
      some (normalize (example_xy.multipliers.get! 0), SparsePoly.zero 2) := by
  native_decide

/-- Adversarial multivariate: wrong multipliers for `xy ∈ ⟨x,y⟩` reject. -/
theorem reject_wrong_witness_xy :
    checkMembershipDetailed
      example_xy.target example_xy.generators
      [SparsePoly.zero 2, SparsePoly.zero 2] = .reject .identityFailed := by
  native_decide

/-- Non-monomial target `x²+xy` divides by monomial `x` to `x+y`. -/
theorem exact_quotient_x2_plus_xy :
    exactQuotientByMonomial?
        { varCount := 2, terms := [
            { coefficient := 1, monomial := ⟨[2, 0]⟩ },
            { coefficient := 1, monomial := ⟨[1, 1]⟩ }] }
        { varCount := 2, terms := [{ coefficient := 1, monomial := ⟨[1, 0]⟩ }] } =
      some (normalize {
        varCount := 2
        terms := [
          { coefficient := 1, monomial := ⟨[1, 0]⟩ },
          { coefficient := 1, monomial := ⟨[0, 1]⟩ }]
      }) := by
  native_decide

/-- IR package: `X₀² − X₁ ∈ ⟨X₀² − X₁⟩` (trivial non-monomial generator). -/
def example_mv_x2_minus_y : MembershipWitness where
  target := {
    varCount := 2
    terms := [
      { coefficient := 1, monomial := ⟨[2, 0]⟩ },
      { coefficient := -1, monomial := ⟨[0, 1]⟩ }
    ]
  }
  generators := [
    {
      varCount := 2
      terms := [
        { coefficient := 1, monomial := ⟨[2, 0]⟩ },
        { coefficient := -1, monomial := ⟨[0, 1]⟩ }
      ]
    }
  ]
  multipliers := [constMv 2 1]

theorem example_mv_x2_minus_y_accepts : example_mv_x2_minus_y.check = true := by
  native_decide

/-- Exact mv division recovers multiplier `1` for the trivial principal case. -/
theorem exact_quotient_mv_x2_minus_y_trivial :
    exactQuotientMv? example_mv_x2_minus_y.target
        (example_mv_x2_minus_y.generators.head!) =
      some (constMv 2 1) := by
  native_decide

/-- Non-trivial: `(X₀² − X₁)·X₀ = X₀³ − X₀·X₁ ∈ ⟨X₀² − X₁⟩`. -/
def example_mv_x3_minus_xy : MembershipWitness where
  target := {
    varCount := 2
    terms := [
      { coefficient := 1, monomial := ⟨[3, 0]⟩ },
      { coefficient := -1, monomial := ⟨[1, 1]⟩ }
    ]
  }
  generators := [
    {
      varCount := 2
      terms := [
        { coefficient := 1, monomial := ⟨[2, 0]⟩ },
        { coefficient := -1, monomial := ⟨[0, 1]⟩ }
      ]
    }
  ]
  multipliers := [
    { varCount := 2, terms := [{ coefficient := 1, monomial := ⟨[1, 0]⟩ }] }
  ]

theorem example_mv_x3_minus_xy_accepts : example_mv_x3_minus_xy.check = true := by
  native_decide

theorem exact_quotient_mv_x3_minus_xy :
    exactQuotientMv? example_mv_x3_minus_xy.target
        (example_mv_x3_minus_xy.generators.head!) =
      some (normalize (example_mv_x3_minus_xy.multipliers.head!)) := by
  native_decide

/-- Fin-3 IR: `X₀·X₁·X₂ ∈ ⟨X₀⟩` via monomial division (`varCount = 3`). -/
def example_mv3_xyz_in_x : MembershipWitness where
  target := {
    varCount := 3
    terms := [{ coefficient := 1, monomial := ⟨[1, 1, 1]⟩ }]
  }
  generators := [
    { varCount := 3, terms := [{ coefficient := 1, monomial := ⟨[1, 0, 0]⟩ }] }
  ]
  multipliers := [
    { varCount := 3, terms := [{ coefficient := 1, monomial := ⟨[0, 1, 1]⟩ }] }
  ]

theorem example_mv3_xyz_in_x_accepts : example_mv3_xyz_in_x.check = true := by
  native_decide

theorem exact_quotient_mv3_xyz_by_x :
    exactQuotientByMonomial? example_mv3_xyz_in_x.target
        (example_mv3_xyz_in_x.generators.head!) =
      some (normalize (example_mv3_xyz_in_x.multipliers.head!)) := by
  native_decide

/-- Two-generator with one non-monomial generator: `X₀³−X₀X₁ ∈ ⟨X₀²−X₁, X₁⟩`. -/
theorem propose_pair_mv_nonmonomial_gen :
    proposePairWitnessMv?
        example_mv_x3_minus_xy.target
        (example_mv_x3_minus_xy.generators.head!)
        { varCount := 2, terms := [{ coefficient := 1, monomial := ⟨[0, 1]⟩ }] } =
      some (normalize (example_mv_x3_minus_xy.multipliers.head!), SparsePoly.zero 2) := by
  native_decide

end MathEvidence.Checkers.IdealMembership
