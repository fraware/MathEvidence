theorem p02CtxSyntax (x : Nat : x = x := by
  rfl

theorem p02CtxExists : ∀ (n : Nat), ∃ m : Nat, m = n := by
  intro n
  exact ⟨n, rfl⟩
