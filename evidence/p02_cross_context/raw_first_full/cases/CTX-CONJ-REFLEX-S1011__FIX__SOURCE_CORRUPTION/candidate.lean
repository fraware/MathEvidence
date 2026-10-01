theorem p02CtxPolicy : True := by
  sorry

theorem p02CtxConj : ∀ (a b : Nat), a = a ∧ a = a := by
  intro a b
  exact ⟨rfl, rfl⟩
