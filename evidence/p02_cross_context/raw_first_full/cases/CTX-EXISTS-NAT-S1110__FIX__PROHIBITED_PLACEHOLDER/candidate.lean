theorem p02CtxSyntax (x : Nat : x = x := by
  rfl

theorem p02CtxElab : True := by
  exact False

theorem p02CtxExists : ∀ (n : Nat), ∃ m : Nat, m = n := by
  exact False
