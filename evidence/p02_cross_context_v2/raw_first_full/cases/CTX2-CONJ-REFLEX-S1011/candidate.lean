theorem p02Ctx2Syntax (x : Nat : x = x := by
  rfl

theorem p02Ctx2Policy : True := by
  sorry

theorem p02Ctx2Conj : ∀ (a b : Nat), a = a ∧ a = a := by
  intro a b
  exact ⟨rfl, rfl⟩
