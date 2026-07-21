(* ::Package:: *)
(* MathEvidence Studio — Wolfram Language surface (Product 09 / Milestone 5)

   Builds on LeanLink + Agent API patterns. No unique mathematical semantics:
   Studio is a client of stable capability / orchestration APIs.

   Epistemic UI states (text + detail required; color alone is insufficient):
     Computed | Tested | Certified | Ambiguous

   HARD RULE: never present Certified without an explicit Lean status of
   witness_verified | soundness_verified | completeness_verified |
   optimality_verified | approximation_certified | native_verified.

   Surface rule: Lean proposition + assumptions always appear before the
   Certified affordance (CertificationSurface transcript order).
*)

BeginPackage["MathEvidenceStudio`"];

MathEvidenceStudio::usage = "MathEvidenceStudio is the Wolfram Studio entry namespace.";
$MathEvidenceAgentBase::usage = "Base URL for the local Agent API (default http://127.0.0.1:8787).";
$MathEvidenceLeanStatus::usage = "Optional Lean replay status string; required for Certified.";

EpistemicFromResultStatus::usage =
  "EpistemicFromResultStatus[resultStatus, leanStatus] → <|Label, Detail, AllowCertified|>.";
StudioStateBadge::usage = "StudioStateBadge[epistemic] formats a text+detail badge.";
ShowLeanProposition::usage =
  "ShowLeanProposition[assoc] displays the exact proposed Lean proposition (Agent/Lean field only).";
ShowAssumptions::usage = "ShowAssumptions[request] lists domainConditions / knownAssumptions / ICs.";
CertificationSurface::usage =
  "CertificationSurface[payload] → ordered transcript: proposition, assumptions, epistemic.";
ProposeCalculusRequest::usage =
  "ProposeCalculusRequest[op, expr, opts] builds an algebra.formal_rational_calculus request skeleton.";
CertifyInLean::usage =
  "CertifyInLean[bundleOrRequest] runs Agent API compute/replay; never labels Certified without Lean.";
InspectBundle::usage = "InspectBundle[bundleDir] displays epistemic state and assumptions.";
ExportTheoremAndBundle::usage =
  "ExportTheoremAndBundle[path, theoremText, bundleAssoc] writes theorem + evidence paths.";
ListStudioCapabilities::usage = "ListStudioCapabilities[] queries Agent API list_capabilities.";

Begin["`Private`"];

$MathEvidenceAgentBase = "http://127.0.0.1:8787";
$MathEvidenceLeanStatus = None;

$LeanOkStatuses = {
  "witness_verified", "soundness_verified", "completeness_verified",
  "optimality_verified", "approximation_certified", "native_verified"
};

Clear[EpistemicFromResultStatus];
EpistemicFromResultStatus[resultStatus_String, leanStatus_: None] := Module[
  {s = ToLowerCase[resultStatus], lean = Replace[leanStatus, None -> ""], leanOk},
  leanOk = MemberQ[$LeanOkStatuses, ToLowerCase[ToString[lean]]];
  Which[
    leanOk,
      <|
        "Label" -> "Certified",
        "Detail" -> "Lean kernel/replay status present: " <> ToString[lean],
        "AllowCertified" -> True
      |>,
    MemberQ[$LeanOkStatuses, s],
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

extractLeanProposition[assoc_Association] := Module[
  {keys = {"leanProposition", "theoremPreview", "proposedLeanProposition"}, v},
  Catch[
    Do[
      v = Lookup[assoc, k, None];
      If[StringQ[v] && StringTrim[v] =!= "", Throw[StringTrim[v]]],
      {k, keys}
    ];
    ""
  ]
];

extractAssumptions[request_Association] := Module[
  {keys = {"knownAssumptions", "domainConditions", "assumptions"}, v},
  Catch[
    Do[
      v = Lookup[request, k, None];
      If[ListQ[v], Throw[v]],
      {k, keys}
    ];
    {}
  ]
];

ShowLeanProposition[assoc_Association] := Module[
  {prop = extractLeanProposition[assoc]},
  Column[{
    Style["Proposed Lean proposition", Bold],
    If[prop === "",
      Style[
        "(Lean proposition not yet available — required before Certified)",
        Gray, Italic
      ],
      Style[prop, "Input"]
    ]
  }]
];

ShowAssumptions[request_Association] := Module[
  {conds = extractAssumptions[request],
   ics = Lookup[request, "initialConditions", {}]},
  Column[{
    Style["Assumptions / side conditions", Bold],
    If[conds === {} || conds === None,
      Style["(none listed — confirm no hidden defaults)", Gray, Italic],
      Column[conds]
    ],
    Style["Initial conditions", Bold],
    If[ics === {} || ics === None, "(none)", Column[ics]]
  }]
];

CertificationSurface[payload_Association] := Module[
  {result, status, lean, prop, assumps, epi, transcript},
  result = Lookup[payload, "agentResult", payload];
  status = ToString[Lookup[result, "resultStatus", Lookup[payload, "resultStatus", "ambiguous"]]];
  lean = Lookup[result, "leanStatus",
    Lookup[payload, "leanStatus", $MathEvidenceLeanStatus]];
  prop = extractLeanProposition[result];
  If[prop === "", prop = extractLeanProposition[payload]];
  assumps = extractAssumptions[If[AssociationQ[Lookup[payload, "request", None]],
    payload["request"], payload]];
  If[assumps === {} && KeyExistsQ[result, "domainConditions"],
    assumps = Lookup[result, "domainConditions", {}]];
  epi = EpistemicFromResultStatus[status, lean];
  If[TrueQ[epi["AllowCertified"]] && prop === "",
    epi = <|
      "Label" -> "Ambiguous",
      "Detail" ->
        "Lean status is present, but the exact Lean proposition is not available yet. Not labeled Certified.",
      "AllowCertified" -> False
    |>
  ];
  transcript = {
    <|"section" -> "leanProposition", "title" -> "Proposed Lean proposition",
      "body" -> If[prop === "",
        "(Lean proposition not yet available — required before Certified)", prop]|>,
    <|"section" -> "assumptions", "title" -> "Assumptions / side conditions",
      "body" -> assumps,
      "emptyNote" -> "(none listed — confirm no hidden defaults)"|>,
    <|"section" -> "epistemicLabel", "title" -> "Epistemic state",
      "body" -> epi["Label"], "detail" -> epi["Detail"],
      "allowCertified" -> epi["AllowCertified"]|>
  };
  <|
    "epistemic" -> epi,
    "leanProposition" -> prop,
    "assumptions" -> assumps,
    "transcript" -> transcript,
    "transcriptOrder" -> {"leanProposition", "assumptions", "epistemicLabel"},
    "certifiedAffordanceIndex" -> 2
  |>
];

ProposeCalculusRequest[op_String, expr_, opts : OptionsPattern[]] := Module[
  {indep = OptionValue["IndependentVar"], dep = OptionValue["DependentVar"],
   vars = OptionValue["Variables"], domain = OptionValue["DomainConditions"],
   candidate = OptionValue["Candidate"], ode = OptionValue["OdeRhs"],
   rec = OptionValue["RecurrenceRhs"], ics = OptionValue["InitialConditions"],
   leanProp = OptionValue["LeanProposition"]},
  <|
    "schemaVersion" -> "0.1.0",
    "capability" -> "algebra.formal_rational_calculus",
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
    "leanProposition" -> leanProp,
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
  "InitialConditions" -> {},
  "LeanProposition" -> None
};

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
  {surface, epi},
  (* Step order matches Product 09 §5; Certified only after Lean status + proposition. *)
  surface = CertificationSurface[payload];
  epi = surface["epistemic"];
  <|
    "epistemic" -> epi,
    "resultStatus" -> Lookup[payload, "resultStatus",
      Lookup[Lookup[payload, "agentResult", <||>], "resultStatus", "ambiguous"]],
    "leanStatus" -> Lookup[payload, "leanStatus",
      Lookup[Lookup[payload, "agentResult", <||>], "leanStatus", $MathEvidenceLeanStatus]],
    "leanProposition" -> surface["leanProposition"],
    "assumptions" -> surface["assumptions"],
    "transcript" -> surface["transcript"],
    "transcriptOrder" -> surface["transcriptOrder"],
    "unresolvedObligations" -> Lookup[
      Lookup[payload, "agentResult", payload], "unresolvedObligations", {}],
    "bundleRef" -> Lookup[Lookup[payload, "agentResult", payload], "bundleRef", None],
    "theoremPreview" -> surface["leanProposition"],
    "certified" -> TrueQ[epi["AllowCertified"]],
    (* Display order: proposition and assumptions before Certified badge. *)
    "display" -> Column[{
      ShowLeanProposition[<|"leanProposition" -> surface["leanProposition"]|>],
      ShowAssumptions[<|"knownAssumptions" -> surface["assumptions"]|>],
      StudioStateBadge[epi]
    }]
  |>
];

InspectBundle[bundleDir_String] := Module[
  {manifestPath = FileNameJoin[{bundleDir, "manifest.json"}],
   requestPath = FileNameJoin[{bundleDir, "request.json"}],
   manifest, request, surface},
  If[!FileExistsQ[manifestPath], Return[$Failed]];
  manifest = Import[manifestPath, "RawJSON"];
  request = If[FileExistsQ[requestPath], Import[requestPath, "RawJSON"], <||>];
  surface = CertificationSurface[<|
    "resultStatus" -> Lookup[manifest, "resultStatus", "ambiguous"],
    "leanStatus" -> Lookup[manifest, "leanStatus", $MathEvidenceLeanStatus],
    "leanProposition" -> Lookup[manifest, "leanProposition",
      Lookup[manifest, "theoremPreview", None]],
    "request" -> If[AssociationQ[request], request, <||>]
  |>];
  Column[{
    (* Proposition + assumptions BEFORE Certified affordance. *)
    ShowLeanProposition[<|"leanProposition" -> surface["leanProposition"]|>],
    ShowAssumptions[If[AssociationQ[request], request, <||>]],
    StudioStateBadge[surface["epistemic"]],
    Style["Capability", Bold],
    Lookup[Lookup[manifest, "capability", <||>], "id", "?"],
    Style["Machine resultStatus", Bold],
    Lookup[manifest, "resultStatus", "ambiguous"],
    Style["Lean status (required for Certified)", Bold],
    ToString[Lookup[manifest, "leanStatus", $MathEvidenceLeanStatus]],
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
