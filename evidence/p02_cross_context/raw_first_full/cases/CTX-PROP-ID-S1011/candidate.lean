theorem p02CtxSyntax (x : Nat : x = x := by
  rfl

theorem p02CtxPolicy : True := by
  sorry

theorem p02CtxProp : ∀ (p : Prop), True → True := by
  intro p h
  exact h
