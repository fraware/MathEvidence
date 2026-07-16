(* Example Studio workflow for Milestone 5 symbolic calculus / Product 09.

   Requires:
   - Agent API: `just agent-api` (optional for InspectBundle on filesystem)
   - This package on $Path

   Get["studio/wolfram/MathEvidenceStudio.wl"]
*)

Needs["MathEvidenceStudio`"];

(* 1. Propose a derivative-candidate request (IR-shaped association). *)
req = ProposeCalculusRequest[
  "derivative_candidate",
  <|"tag" -> "pow", "base" -> <|"tag" -> "var", "name" -> "x"|>, "exp" -> 2|>,
  "Candidate" -> <|"tag" -> "mul", "left" -> <|"tag" -> "int", "value" -> "2"|>,
    "right" -> <|"tag" -> "var", "name" -> "x"|>|>,
  "DomainConditions" -> {},
  "LeanProposition" -> "∀ (x : ℚ), deriv (fun x => x^2) x = 2 * x"
];

(* Proposition + assumptions before any Certified affordance. *)
ShowLeanProposition[req]
ShowAssumptions[req]

(* 2. Without Lean status, computed results stay Computed / Ambiguous — never Certified. *)
EpistemicFromResultStatus["computed"]
EpistemicFromResultStatus["soundness_verified"]  (* Ambiguous: Lean missing *)
EpistemicFromResultStatus["soundness_verified", "soundness_verified"]  (* gate ok *)

(* 3. Full surface: Lean without proposition → Ambiguous; with both → Certified. *)
CertificationSurface[<|"resultStatus" -> "soundness_verified",
  "leanStatus" -> "soundness_verified"|>]
CertificationSurface[<|"resultStatus" -> "soundness_verified",
  "leanStatus" -> "soundness_verified",
  "leanProposition" -> "∀ (x : ℚ), deriv (fun x => x^2) x = 2 * x",
  "request" -> req|>]

(* 4. Inspect a committed offline bundle (path relative to repo root). *)
(* InspectBundle["evidence/examples/calculus_derivative_x2"] *)

(* 5. CertifyInLean refuses Certified unless leanStatus + proposition. *)
CertifyInLean[<|"resultStatus" -> "computed", "domainConditions" -> {}|>]
