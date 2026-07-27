/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.Polynomial.Normalize
import MathEvidence.Checkers.IdealMembership.Check

/-!
# Untrusted ideal-membership witness search (not part of the trusted checker)

`lean_reference_search` baseline used by `mathevidence_ideal`. External backends
(SymPy/Sage/Mathematica) live in Python adapters.
-/

namespace MathEvidence.Checkers.IdealMembership.Search

open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership

/-- Leading term of a univariate sparse polynomial. -/
def leadingUnivariate? (p : SparsePoly 1) : Option (Int × Nat) :=
  Id.run do
    let mut best : Option (Int × Nat) := none
    for t in p.normalize.terms do
      let e := t.monomial.exponents[0]
      match best with
      | none => best := some (t.coefficient, e)
      | some (_, be) =>
        if e > be then best := some (t.coefficient, e)
    pure best

/-- Exact univariate division over ℤ. -/
def exactQuotientUnivariate? (f g : SparsePoly 1) : Option (SparsePoly 1) :=
  match leadingUnivariate? g with
  | none => none
  | some (lcG, degG) =>
    if lcG == 0 then none
    else
      Id.run do
        let mut rem := f.normalize
        let mut qTerms : List (Term 1) := []
        let mut guard := f.normalize.terms.length + 8
        while guard > 0 do
          guard := guard - 1
          match leadingUnivariate? rem with
          | none =>
            return some (SparsePoly.normalize ⟨qTerms⟩)
          | some (lcR, degR) =>
            if degR < degG then return none
            if lcR % lcG != 0 then return none
            let c := lcR / lcG
            let e := degR - degG
            let mon : Term 1 :=
              { coefficient := c, monomial := ⟨⟨[e], rfl⟩⟩ }
            qTerms := qTerms ++ [mon]
            let step := SparsePoly.mul ⟨[mon]⟩ g
            rem := SparsePoly.sub rem step
        pure none

/-- Exact singleton quotient dispatch. -/
def proposeSingletonWitness? {m : Nat} (f g : SparsePoly m) : Option (SparsePoly m) :=
  if h : m = 1 then
    let f1 : SparsePoly 1 := cast (by rw [h]) f
    let g1 : SparsePoly 1 := cast (by rw [h]) g
    (exactQuotientUnivariate? f1 g1).map fun q => cast (by rw [h]) q
  else if f.normalize == g.normalize then
    some (SparsePoly.C m 1)
  else if checkMembership f #[g] #[SparsePoly.C m 1] then
    some (SparsePoly.C m 1)
  else if checkMembership f #[g] #[f] then
    some f
  else
    none

/-- Pair witness: try principal paths, product witnesses, then small constant search. -/
def proposePairWitness? {m : Nat} (f g1 g2 : SparsePoly m) :
    Option (SparsePoly m × SparsePoly m) :=
  Id.run do
    let mut found : Option (SparsePoly m × SparsePoly m) := none
    match proposeSingletonWitness? f g1 with
    | some q =>
      if checkMembership f #[g1, g2] #[q, SparsePoly.zero m] then
        found := some (q, SparsePoly.zero m)
    | none => pure ()
    if found.isNone then
      match proposeSingletonWitness? f g2 with
      | some q =>
        if checkMembership f #[g1, g2] #[SparsePoly.zero m, q] then
          found := some (SparsePoly.zero m, q)
      | none => pure ()
    -- Product / monomial shortcuts: f = g2·g1 or f = g1·g2 (e.g. X*Y ∈ ⟨X,Y⟩).
    if found.isNone then
      if checkMembership f #[g1, g2] #[g2, SparsePoly.zero m] then
        found := some (g2, SparsePoly.zero m)
      else if checkMembership f #[g1, g2] #[g1, SparsePoly.zero m] then
        found := some (g1, SparsePoly.zero m)
      else if checkMembership f #[g1, g2] #[SparsePoly.zero m, g1] then
        found := some (SparsePoly.zero m, g1)
      else if checkMembership f #[g1, g2] #[SparsePoly.zero m, g2] then
        found := some (SparsePoly.zero m, g2)
    if found.isNone then
      for c in [(-4 : Int), -2, -1, 1, 2, 4] do
        if found.isSome then break
        let q1 := SparsePoly.C m c
        let rem := SparsePoly.sub f (SparsePoly.mul q1 g1)
        match proposeSingletonWitness? rem g2 with
        | some q2 =>
          if checkMembership f #[g1, g2] #[q1, q2] then
            found := some (q1, q2)
        | none => pure ()
    pure found

/-- Triple witness: principal / product shortcuts (e.g. X*Y*Z ∈ ⟨X,Y,Z⟩). -/
def proposeTripleWitness? {m : Nat} (f g1 g2 g3 : SparsePoly m) :
    Option (SparsePoly m × SparsePoly m × SparsePoly m) :=
  Id.run do
    let z := SparsePoly.zero m
    let mut found : Option (SparsePoly m × SparsePoly m × SparsePoly m) := none
    -- Product shortcuts: f = g1·(g2·g3) etc.
    let candidates : List (SparsePoly m × SparsePoly m × SparsePoly m) :=
      [ (g2.mul g3, z, z)
      , (g3.mul g2, z, z)
      , (z, g1.mul g3, z)
      , (z, g3.mul g1, z)
      , (z, z, g1.mul g2)
      , (z, z, g2.mul g1)
      ]
    for c in candidates do
      if found.isSome then break
      let (q1, q2, q3) := c
      if checkMembership f #[g1, g2, g3] #[q1, q2, q3] then
        found := some (q1, q2, q3)
    if found.isNone then
      match proposeSingletonWitness? f g1 with
      | some q =>
        if checkMembership f #[g1, g2, g3] #[q, z, z] then
          found := some (q, z, z)
      | none => pure ()
    if found.isNone then
      match proposePairWitness? f g1 g2 with
      | some (q1, q2) =>
        if checkMembership f #[g1, g2, g3] #[q1, q2, z] then
          found := some (q1, q2, z)
      | none => pure ()
    pure found

/-- Alias: Lean-side baseline backend name. -/
def lean_reference_search {m : Nat} (f : SparsePoly m) (gens : Array (SparsePoly m)) :
    Option (Array (SparsePoly m)) :=
  match gens.size with
  | 1 => (proposeSingletonWitness? f gens[0]!).map fun q => #[q]
  | 2 => (proposePairWitness? f gens[0]! gens[1]!).map fun (q1, q2) => #[q1, q2]
  | 3 =>
    (proposeTripleWitness? f gens[0]! gens[1]! gens[2]!).map fun (q1, q2, q3) =>
      #[q1, q2, q3]
  | _ => none

end MathEvidence.Checkers.IdealMembership.Search
