theorem p02Ctx2Syntax (x : Nat : x = x := by
  rfl

theorem p02Ctx2Policy : True := by
  sorry

theorem p02Ctx2Exists : ∀ (n : Nat), ∃ m : Nat, m = m := by
  exact False
