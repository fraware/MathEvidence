(* Example Studio workflow for Milestone 5 symbolic calculus.

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
  "DomainConditions" -> {}
];

ShowAssumptions[req]

(* 2. Without Lean status, computed results stay Computed / Ambiguous — never Certified. *)
EpistemicFromResultStatus["computed"]
EpistemicFromResultStatus["soundness_verified"]  (* Ambiguous: Lean missing *)
EpistemicFromResultStatus["soundness_verified", "soundness_verified"]  (* Certified *)

(* 3. Inspect a committed offline bundle (path relative to repo root). *)
(* InspectBundle["evidence/examples/calculus_derivative_x2"] *)

(* 4. CertifyInLean refuses Certified unless leanStatus is set. *)
CertifyInLean[<|"resultStatus" -> "computed", "domainConditions" -> {}|>]
