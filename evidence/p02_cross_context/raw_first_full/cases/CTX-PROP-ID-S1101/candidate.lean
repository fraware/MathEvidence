theorem p02CtxSyntax (x : Nat : x = x := by
  rfl

theorem p02CtxElab : True := by
  exact False

theorem p02CtxProp : ∀ (p : Prop), True → True := by
  exact False
