theorem p02CtxSyntax (x : Nat : x = x := by
  rfl

theorem p02CtxPolicy : True := by
  sorry

theorem p02CtxElab : True := by
  exact False

theorem p02CtxConj : ∀ (a b : Nat), a = a ∧ a = a := by
  exact False
