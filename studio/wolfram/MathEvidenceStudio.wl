(* ::Package:: *)
(* MathEvidence Studio — Wolfram Language surface (Product 09 / Milestone 5)

   Builds on LeanLink + Agent API patterns. No unique mathematical semantics:
   Studio is a client of stable capability / orchestration APIs.

   Epistemic UI states (text + detail required; color alone is insufficient):
     Computed | Tested | Certified | Ambiguous

   HARD RULE: never present Certified without an explicit Lean status of
   witness_verified | soundness_verified | completeness_verified |
   optimality_verified | approximation_certified | native_verified.
*)

BeginPackage["MathEvidenceStudio`"];

MathEvidenceStudio::usage = "MathEvidenceStudio is the Wolfram Studio entry namespace.";
$MathEvidenceAgentBase::usage = "Base URL for the local Agent API (default http://127.0.0.1:8787).";
$MathEvidenceLeanStatus::usage = "Optional Lean replay status string; required for Certified.";

EpistemicFromResultStatus::usage =
  "EpistemicFromResultStatus[resultStatus, leanStatus] → <|Label, Detail, AllowCertified|>.";
StudioStateBadge::usage = "StudioStateBadge[epistemic] formats a text+detail badge.";
ProposeCalculusRequest::usage =
  "ProposeCalculusRequest[op, expr, opts] builds an analysis.symbolic_calculus request skeleton.";
CertifyInLean::usage =
  "CertifyInLean[bundleOrRequest] runs Agent API compute/replay; never labels Certified without Lean.";
InspectBundle::usage = "InspectBundle[bundleDir] displays epistemic state and assumptions.";
ExportTheoremAndBundle::usage =
  "ExportTheoremAndBundle[path, theoremText, bundleAssoc] writes theorem + evidence paths.";
ShowAssumptions::usage = "ShowAssumptions[request] lists domainConditions / ICs.";
ListStudioCapabilities::usage = "ListStudioCapabilities[] queries Agent API list_capabilities.";

Begin["`Private`"];

$MathEvidenceAgentBase = "http://127.0.0.1:8787";
$MathEvidenceLeanStatus = None;

Clear[EpistemicFromResultStatus];
EpistemicFromResultStatus[resultStatus_String, leanStatus_: None] := Module[
  {s = ToLowerCase[resultStatus], lean = Replace[leanStatus, None -> ""], leanOk},
  leanOk = MemberQ[
    {
      "witness_verified", "soundness_verified", "completeness_verified",
      "optimality_verified", "approximation_certified", "native_verified"
    },
    ToLowerCase[ToString[lean]]
  ];
  Which[
    leanOk,
      <|
        "Label" -> "Certified",
        "Detail" -> "Lean kernel/replay status present: " <> ToString[lean],
        "AllowCertified" -> True
      |>,
    MemberQ[
      {
        "soundness_verified", "witness_verified", "completeness_verified",
        "optimality_verified", "approximation_certified", "native_verified"
      },
      s
    ],
      (* Manifest claims verified, but Studio refuses Certified without Lean field. *)
      <|
        "Label" -> "Ambiguous",
        "Detail" ->
          "Manifest claims verified status '" <> s <>
          "' but Lean status is missing. Not labeled Certified.",
        "AllowCertified" -> False
      |>,
    s === "tested",
      <|
        "Label" -> "Tested",
        "Detail" -> "Offline schema/digest checks succeeded; Lean certification not asserted.",
        "AllowCertified" -> False
      |>,
    s === "computed",
      <|
        "Label" -> "Computed",
        "Detail" -> "Backend/candidate output only. Not Lean-certified.",
        "AllowCertified" -> False
      |>,
    True,
      <|
        "Label" -> "Ambiguous",
        "Detail" -> "Status is ambiguous, rejected, unsupported, or missing: " <> s,
        "AllowCertified" -> False
      |>
  ]
];

StudioStateBadge[epi_Association] :=
  Column[{
    Style[epi["Label"], Bold, 14],
    Style[epi["Detail"], Gray, 11]
  }];

ProposeCalculusRequest[op_String, expr_, opts : OptionsPattern[]] := Module[
  {indep = OptionValue["IndependentVar"], dep = OptionValue["DependentVar"],
   vars = OptionValue["Variables"], domain = OptionValue["DomainConditions"],
   candidate = OptionValue["Candidate"], ode = OptionValue["OdeRhs"],
   rec = OptionValue["RecurrenceRhs"], ics = OptionValue["InitialConditions"]},
  <|
    "schemaVersion" -> "0.1.0",
    "capability" -> "analysis.symbolic_calculus",
    "capabilityVersion" -> "0.1.0",
    "operation" -> op,
    "variables" -> vars,
    "independentVar" -> indep,
    "dependentVar" -> dep,
    "expr" -> expr,
    "candidate" -> candidate,
    "domainConditions" -> domain,
    "odeRhs" -> ode,
    "recurrenceRhs" -> rec,
    "initialConditions" -> ics,
    "requestedClaim" -> "candidate",
    "resourcePolicy" -> <|"maxWallTimeMs" -> 60000, "maxOutputBytes" -> 1048576|>
  |>
];
Options[ProposeCalculusRequest] = {
  "IndependentVar" -> "x",
  "DependentVar" -> "y",
  "Variables" -> {<|"name" -> "x", "type" -> "Rat"|>},
  "DomainConditions" -> {},
  "Candidate" -> None,
  "OdeRhs" -> None,
  "RecurrenceRhs" -> None,
  "InitialConditions" -> {}
};

ShowAssumptions[request_Association] := Module[
  {conds = Lookup[request, "domainConditions", {}],
   ics = Lookup[request, "initialConditions", {}]},
  Column[{
    Style["Domain / singularity / branch conditions", Bold],
    If[conds === {} || conds === None, "(none listed — only valid when no divisions)", Column[conds]],
    Style["Initial conditions", Bold],
    If[ics === {} || ics === None, "(none)", Column[ics]]
  }]
];

agentPost[path_String, body_Association] := Module[
  {url = StringTrim[$MathEvidenceAgentBase, "/"] <> path, raw},
  raw = URLRead[
    HTTPRequest[url, <|Method -> "POST", "Body" -> ExportString[body, "RawJSON"],
      "ContentType" -> "application/json"|>],
    "Body"
  ];
  ImportString[raw, "RawJSON"]
];

ListStudioCapabilities[] := agentPost["/v1/operations/list_capabilities", <||>];

CertifyInLean[payload_Association] := Module[
  {result, status, lean, epi},
  (* Step order matches Product 09 §5; Certified only after Lean status. *)
  result = Lookup[payload, "agentResult", payload];
  status = ToString[Lookup[result, "resultStatus", "ambiguous"]];
  lean = Lookup[result, "leanStatus", $MathEvidenceLeanStatus];
  epi = EpistemicFromResultStatus[status, lean];
  <|
    "epistemic" -> epi,
    "resultStatus" -> status,
    "leanStatus" -> lean,
    "unresolvedObligations" -> Lookup[result, "unresolvedObligations", {}],
    "assumptions" -> Lookup[result, "domainConditions", Lookup[payload, "domainConditions", {}]],
    "bundleRef" -> Lookup[result, "bundleRef", None],
    "theoremPreview" -> Lookup[result, "theoremPreview", None],
    "certified" -> TrueQ[epi["AllowCertified"]]
  |>
];

InspectBundle[bundleDir_String] := Module[
  {manifestPath = FileNameJoin[{bundleDir, "manifest.json"}],
   requestPath = FileNameJoin[{bundleDir, "request.json"}],
   manifest, request, status, lean, epi},
  If[!FileExistsQ[manifestPath], Return[$Failed]];
  manifest = Import[manifestPath, "RawJSON"];
  request = If[FileExistsQ[requestPath], Import[requestPath, "RawJSON"], <||>];
  status = ToString[Lookup[manifest, "resultStatus", "ambiguous"]];
  lean = Lookup[manifest, "leanStatus", $MathEvidenceLeanStatus];
  epi = EpistemicFromResultStatus[status, lean];
  Column[{
    StudioStateBadge[epi],
    Style["Capability", Bold],
    Lookup[Lookup[manifest, "capability", <||>], "id", "?"],
    Style["Machine resultStatus", Bold],
    status,
    Style["Lean status (required for Certified)", Bold],
    ToString[lean],
    ShowAssumptions[If[AssociationQ[request], request, <||>]],
    Style["Request digest", Bold],
    Lookup[manifest, "requestDigest", ""]
  }]
];

ExportTheoremAndBundle[dir_String, theoremText_String, bundle_Association] := Module[
  {},
  If[!DirectoryQ[dir], CreateDirectory[dir]];
  Export[FileNameJoin[{dir, "theorem.lean"}], theoremText, "Text"];
  Export[FileNameJoin[{dir, "bundle.json"}], bundle, "RawJSON"];
  dir
];

End[];
EndPackage[];
