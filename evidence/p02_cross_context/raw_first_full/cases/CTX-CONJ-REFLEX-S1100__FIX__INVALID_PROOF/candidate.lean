theorem p02CtxSyntax (x : Nat : x = x := by
  rfl

theorem p02CtxConj : ∀ (a b : Nat), a = a ∧ b = b := by
  intro a b
  exact ⟨rfl, rfl⟩
