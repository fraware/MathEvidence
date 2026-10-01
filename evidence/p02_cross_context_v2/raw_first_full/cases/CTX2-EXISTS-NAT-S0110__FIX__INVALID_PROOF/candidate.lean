theorem p02Ctx2Policy : True := by
  sorry

theorem p02Ctx2Exists : ∀ (n : Nat), ∃ m : Nat, m = n := by
  intro n
  exact ⟨n, rfl⟩
