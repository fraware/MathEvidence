theorem p02Ctx2Syntax (x : Nat : x = x := by
  rfl

theorem p02Ctx2Exists : ∀ (n : Nat), ∃ m : Nat, m = n := by
  intro n
  exact ⟨n, rfl⟩
