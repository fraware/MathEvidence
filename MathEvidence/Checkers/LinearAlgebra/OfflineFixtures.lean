/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.LinearAlgebra.ReplaySound
import MathEvidence.Checkers.LinearAlgebra.Tests

/-!
# Offline fixtures for LA kernel replay (ME-RV-041)

Hand-written request/certificate pairs used by generated replay modules.
Authority is `replaySound` after `checkBool = true`.
-/

namespace MathEvidence.Checkers.LinearAlgebra.OfflineFixtures

open MathEvidence.Checkers.LinearAlgebra
open MathEvidence.Checkers.LinearAlgebra.Tests

abbrev req_inv := Tests.req_inv
abbrev cert_inv := Tests.cert_inv
abbrev req_sys := Tests.req_sys
abbrev cert_sys := Tests.cert_sys
abbrev req_ker := Tests.req_ker
abbrev cert_ker := Tests.cert_ker
abbrev req_det := Tests.req_det
abbrev cert_det := Tests.cert_det

theorem replay_inv_sound :
    Claim.proposition req_inv.claim cert_inv.inverse cert_inv.vector :=
  replaySound req_inv cert_inv Tests.replay_inv

theorem replay_sys_sound :
    Claim.proposition req_sys.claim cert_sys.inverse cert_sys.vector :=
  replaySound req_sys cert_sys Tests.replay_sys

theorem replay_ker_sound :
    Claim.proposition req_ker.claim cert_ker.inverse cert_ker.vector :=
  replaySound req_ker cert_ker Tests.replay_ker

theorem replay_det_sound :
    Claim.proposition req_det.claim cert_det.inverse cert_det.vector :=
  replaySound req_det cert_det Tests.replay_det

end MathEvidence.Checkers.LinearAlgebra.OfflineFixtures
