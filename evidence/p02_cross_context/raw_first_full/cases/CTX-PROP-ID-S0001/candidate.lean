theorem p02CtxProp : ∀ (p : Prop), True → True := by
  intro p h
  exact h
