theorem p02Ctx2Prop : ∀ (p : Prop), p → p := by
  intro p h
  exact h
