theorem p02CtxPolicy : True := by
  sorry

theorem p02CtxExists : ∀ (n : Nat), ∃ m : Nat, m = m := by
  intro n
  exact ⟨n, rfl⟩
