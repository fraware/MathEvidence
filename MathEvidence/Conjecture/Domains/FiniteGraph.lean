/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Conjecture.Engine
import MathEvidence.Conjecture.Precision
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.Checkers.Counterexample.Soundness

namespace MathEvidence.Conjecture.Domains.FiniteGraph

open MathEvidence.IR.FinitePredicate
open MathEvidence.Checkers.Counterexample
open MathEvidence.Conjecture

/-!
# Finite simple-graph domain plugin (Product 04 primary vertical scaffold)

Formal objects are undirected loopless graphs on `Fin n`, encoded by the upper
triangle of the adjacency matrix (one `Bool` per unordered pair `{i,j}` with
`i < j`). Executable instances map to `FinitePredicate` claims so falsification
still goes through Lean `checkBool`.

This is the **primary** Conjecture domain scaffold. The Nat-bounded demos in
`Conjecture.Tests` remain regression fixtures only — not the product vertical.
-/

/-- Number of undirected edges among `n` vertices: `n.choose 2`. -/
def edgeSlotCount : Nat → Nat
  | 0 | 1 => 0
  | n + 2 => edgeSlotCount (n + 1) + (n + 1)

/-- Formal object: simple undirected graph on `Fin n`. -/
structure Object (n : Nat) where
  /-- Upper-triangle edge bits; length must equal `edgeSlotCount n`. -/
  upperTriangle : List Bool
  deriving DecidableEq, Repr, Inhabited

/-- Well-formedness of a compact graph encoding. -/
def Object.wellFormed {n : Nat} (g : Object n) : Bool :=
  decide (g.upperTriangle.length = edgeSlotCount n)

/-- Edge count (number of `true` upper-triangle bits). -/
def Object.edgeCount {n : Nat} (g : Object n) : Nat :=
  g.upperTriangle.foldl (fun acc b => if b then acc + 1 else acc) 0

/-- Empty graph on `n` vertices. -/
def emptyGraph (n : Nat) : Object n where
  upperTriangle := List.replicate (edgeSlotCount n) false

theorem emptyGraph3_wellFormed :
    (emptyGraph 3).wellFormed = true := by native_decide

theorem emptyGraph3_edgeCount :
    (emptyGraph 3).edgeCount = 0 := by native_decide

/-- Map a graph object to a Counterexample assignment (one Bool per edge slot). -/
def Object.toAssignment {n : Nat} (g : Object n) : Assignment :=
  g.upperTriangle.map Val.bool

/-- Rebuild a graph from a well-typed Bool assignment of the right length. -/
def ofAssignment? (n : Nat) (σ : Assignment) : Option (Object n) :=
  let bits := σ.filterMap fun
    | .bool b => some b
    | _ => none
  if bits.length = σ.length ∧ bits.length = edgeSlotCount n then
    some ⟨bits⟩
  else
    none

/-- Domain family: simple graphs on three vertices (three possible edges). -/
def family3 : FinitePredicateFamily where
  id := "finite.simple_graph_fin3"
  varNames := ["e01", "e02", "e12"]
  domains := [{ ty := .bool }, { ty := .bool }, { ty := .bool }]
  duplicates := .rejectExactDuplicates
  enumerateBound := 8

/-- False candidate: every 3-vertex simple graph has at least one edge.

Encoded as the finite predicate `e01 ∨ e02 ∨ e12` (at least one edge present).
The empty graph falsifies it after Lean `checkBool`.
-/
def pred_has_edge : Pred :=
  .or (.eq (.var 0) (.lit (.bool true)))
    (.or (.eq (.var 1) (.lit (.bool true)))
      (.eq (.var 2) (.lit (.bool true))))

def claim_has_edge : Claim := family3.toClaim pred_has_edge

def req_has_edge : Request := family3.toRequest pred_has_edge

/-- Empty-graph witness (all edge bits false). -/
def cert_empty : Certificate where
  requestDigest := req_has_edge.requestDigest
  witness := (emptyGraph 3).toAssignment

theorem empty_assignment_matches :
    (emptyGraph 3).toAssignment = [.bool false, .bool false, .bool false] := by
  native_decide

theorem cert_empty_accepted :
    checkBool req_has_edge cert_empty = true := by
  native_decide

/-- Certified falsification path: empty graph refutes "always has an edge". -/
def falsify_has_edge_episode (e : Episode) : Episode :=
  certifyRefutation e req_has_edge cert_empty "cex_graph3_empty"

theorem falsify_has_edge_state :
    (falsify_has_edge_episode
      (toCandidate (observePattern family3.id pred_has_edge))).state = .falsified := by
  native_decide

theorem falsify_has_edge_sound
    (h : checkBool req_has_edge cert_empty = true) :
    Claim.proposition req_has_edge.claim cert_empty.witness :=
  checkBool_sound req_has_edge cert_empty h

/-- Bridge: empty formal object yields the certified Counterexample witness. -/
theorem empty_object_to_certified_witness :
    ofAssignment? 3 cert_empty.witness = some (emptyGraph 3) ∧
      checkBool req_has_edge cert_empty = true := by
  native_decide

/-- Primary-vertical campaign slice (graph family only). -/
def campaignDemo : Campaign :=
  let C0 : Campaign := { family := family3 }
  let eFalse :=
    falsify_has_edge_episode
      (toCandidate (observePattern family3.id pred_has_edge))
  C0.addEpisode eFalse

theorem campaign_falsified :
    let A := campaignDemo.precisionAccounting
    A.proposed = 1 ∧ A.falsified = 1 ∧ A.formallyProved = 0 := by
  native_decide

end MathEvidence.Conjecture.Domains.FiniteGraph
