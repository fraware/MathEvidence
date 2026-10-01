theorem p02CtxSyntax (x : Nat : x = x := by
  rfl

theorem p02CtxProp : ∀ (p : Prop), p → p := by
  intro p h
  exact h
