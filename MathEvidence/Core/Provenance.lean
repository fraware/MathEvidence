/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.Core

/-- Backend identity recorded for provenance (never theorem-trusted). -/
structure BackendProvenance where
  name : String
  version : String := ""
  deriving DecidableEq, Repr, Inhabited

/-- Provenance required on evidence bundles (schema-aligned). -/
structure Provenance where
  leanVersion : String
  libraryRevision : String
  checkerVersion : String
  backend : Option BackendProvenance := none
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.Core
