/--
axiom DocGhost : True
-/
theorem holdoutProp (p : Prop) (hp : p) : p := by
  exact hp
