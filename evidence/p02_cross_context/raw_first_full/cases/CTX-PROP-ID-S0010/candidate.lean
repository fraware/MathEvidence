theorem p02CtxPolicy : True := by
  sorry

theorem p02CtxProp : ∀ (p : Prop), p → p := by
  intro p h
  exact h
