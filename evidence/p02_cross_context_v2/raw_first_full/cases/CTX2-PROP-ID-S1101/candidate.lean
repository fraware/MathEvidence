theorem p02Ctx2Syntax (x : Nat : x = x := by
  rfl

theorem p02Ctx2Prop : ∀ (p : Prop), True → True := by
  exact False
