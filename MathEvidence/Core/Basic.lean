/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.AssuranceMode
import MathEvidence.Core.Bundle
import MathEvidence.Core.CanonicalJson
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.CertificationRecord
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest
import MathEvidence.Core.EnvironmentLock
import MathEvidence.Core.ErrorCode
import MathEvidence.Core.EvidenceId
import MathEvidence.Core.ExprSerialize
import MathEvidence.Core.ExprSerializeTests
import MathEvidence.Core.JsonCanonical
import MathEvidence.Core.JsonCanonicalTests
import MathEvidence.Core.Provenance
import MathEvidence.Core.Receipt
import MathEvidence.Core.ReplayTarget
import MathEvidence.Core.ResultStatus
import MathEvidence.Core.TheoremIdentity

/-!
# MathEvidence.Core

Solver-independent protocol types (Project Spec §§7–8, §13):

* claim classes, result status, assurance modes
* capability identifiers and provenance
* evidence identifiers and bundle metadata
* stable error codes
* SHA-256 digest helpers and Lean-side canonical JSON fragments
-/

namespace MathEvidence.Core

/-- Package marker. -/
def packageName : String := "MathEvidence.Core"

end MathEvidence.Core
