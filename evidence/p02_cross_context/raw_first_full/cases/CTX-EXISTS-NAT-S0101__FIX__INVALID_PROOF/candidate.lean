theorem p02CtxExists : ∀ (n : Nat), ∃ m : Nat, m = m := by
  intro n
  exact ⟨n, rfl⟩
