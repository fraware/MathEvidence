theorem p02CtxSyntax (x : Nat : x = x := by
  rfl

theorem p02CtxConj : ∀ (a b : Nat), a = a ∧ a = a := by
  intro a b
  exact ⟨rfl, rfl⟩
