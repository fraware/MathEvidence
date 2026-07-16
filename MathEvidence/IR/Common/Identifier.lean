/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
namespace MathEvidence.IR

/-- Stable identifier placeholder for IR entities. -/
structure Identifier where
  name : String
  deriving DecidableEq, Repr

end MathEvidence.IR
