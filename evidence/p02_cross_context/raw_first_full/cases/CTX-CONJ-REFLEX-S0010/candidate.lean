theorem p02CtxPolicy : True := by
  sorry

theorem p02CtxConj : ∀ (a b : Nat), a = a ∧ b = b := by
  intro a b
  exact ⟨rfl, rfl⟩
