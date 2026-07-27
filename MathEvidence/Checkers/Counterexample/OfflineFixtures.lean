/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Counterexample.ReplaySound
import MathEvidence.Checkers.Counterexample.Tests

/-!
# Offline fixtures for CEX kernel replay (ME-RV-043)
-/

namespace MathEvidence.Checkers.Counterexample.OfflineFixtures

open MathEvidence.Checkers.Counterexample
open MathEvidence.Checkers.Counterexample.Tests

abbrev req_nat_eq0 := Tests.req_nat_eq0
abbrev cert_nat_eq0 := Tests.cert_nat_eq0
abbrev req_bool := Tests.req_bool
abbrev cert_bool := Tests.cert_bool

theorem replay_nat_eq0_sound :
    Claim.proposition req_nat_eq0.claim cert_nat_eq0.witness :=
  replaySound req_nat_eq0 cert_nat_eq0 Tests.replay_nat_eq0

theorem replay_bool_sound :
    Claim.proposition req_bool.claim cert_bool.witness :=
  replaySound req_bool cert_bool Tests.replay_bool

end MathEvidence.Checkers.Counterexample.OfflineFixtures
