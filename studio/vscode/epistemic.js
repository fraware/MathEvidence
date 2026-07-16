"use strict";

/**
 * Map ResultStatus / manifest fields to Product 09 epistemic UI states.
 * Color alone is insufficient — always pair with text.
 *
 * HARD RULE (Product 09): never present Certified without Lean status.
 * Surface rule: Lean proposition + assumptions always precede Certified affordance
 * (see buildCertificationSurface).
 */

const LEAN_OK_STATUSES = [
  "soundness_verified",
  "witness_verified",
  "completeness_verified",
  "optimality_verified",
  "approximation_certified",
  "native_verified",
];

/**
 * @param {string|undefined|null} leanStatus
 * @returns {boolean}
 */
function leanStatusAllowsCertified(leanStatus) {
  const lean = (leanStatus || "").toLowerCase();
  return LEAN_OK_STATUSES.includes(lean);
}

/**
 * @param {string|undefined} resultStatus
 * @param {string|undefined|null} leanStatus
 * @returns {{ label: "Computed"|"Tested"|"Certified"|"Ambiguous", detail: string, allowCertified: boolean }}
 */
function epistemicFromResultStatus(resultStatus, leanStatus) {
  const s = (resultStatus || "").toLowerCase();
  const leanOk = leanStatusAllowsCertified(leanStatus);

  if (leanOk) {
    return {
      label: "Certified",
      detail: `Lean status present: ${leanStatus}.`,
      allowCertified: true,
    };
  }

  if (LEAN_OK_STATUSES.includes(s)) {
    return {
      label: "Ambiguous",
      detail:
        "Manifest claims a verified status, but Lean status is missing. Not labeled Certified.",
      allowCertified: false,
    };
  }
  if (s === "tested") {
    return {
      label: "Tested",
      detail:
        "Offline schema/digest checks succeeded; Lean certification not asserted.",
      allowCertified: false,
    };
  }
  if (s === "computed") {
    return {
      label: "Computed",
      detail: "Backend/candidate output only. Not Lean-certified.",
      allowCertified: false,
    };
  }
  if (s === "ambiguous" || s === "rejected" || s === "unsupported" || !s) {
    return {
      label: "Ambiguous",
      detail: "Status is ambiguous, rejected, unsupported, or missing.",
      allowCertified: false,
    };
  }
  return {
    label: "Ambiguous",
    detail: `Unrecognized resultStatus: ${resultStatus}`,
    allowCertified: false,
  };
}

/**
 * @param {object|null|undefined} request
 * @returns {any[]}
 */
function extractAssumptions(request) {
  if (!request || typeof request !== "object") {
    return [];
  }
  for (const key of ["knownAssumptions", "domainConditions", "assumptions"]) {
    const raw = request[key];
    if (Array.isArray(raw)) {
      return raw.slice();
    }
  }
  return [];
}

/**
 * Prefer explicit Lean/Agent fields; never invent checker semantics.
 * @param {object} opts
 * @returns {string}
 */
function extractLeanProposition(opts = {}) {
  const {
    leanProposition,
    theoremPreview,
    request,
    manifest,
  } = opts;
  const candidates = [
    leanProposition,
    theoremPreview,
    manifest && manifest.leanProposition,
    manifest && manifest.theoremPreview,
    request && request.leanProposition,
    request && request.theoremPreview,
    request && request.proposedLeanProposition,
  ];
  for (const c of candidates) {
    if (typeof c === "string" && c.trim()) {
      return c.trim();
    }
  }
  return "";
}

/**
 * Ordered certification surface: proposition → assumptions → epistemic label.
 * Certified affordance only after proposition + assumptions sections.
 * If Lean would allow Certified but proposition text is missing → Ambiguous.
 *
 * @param {object} opts
 * @returns {object}
 */
function buildCertificationSurface(opts = {}) {
  const {
    resultStatus,
    leanStatus,
    leanProposition,
    theoremPreview,
    request,
    manifest,
    assumptions,
  } = opts;

  const proposition = extractLeanProposition({
    leanProposition,
    theoremPreview,
    request,
    manifest,
  });
  const assumps =
    assumptions !== undefined && assumptions !== null
      ? assumptions.slice()
      : extractAssumptions(request);

  let epi = epistemicFromResultStatus(resultStatus, leanStatus);
  if (epi.allowCertified && !proposition) {
    epi = {
      label: "Ambiguous",
      detail:
        "Lean status is present, but the exact Lean proposition is not available yet. Not labeled Certified.",
      allowCertified: false,
    };
  }

  const transcript = [
    {
      section: "leanProposition",
      title: "Proposed Lean proposition",
      body:
        proposition ||
        "(Lean proposition not yet available — required before Certified)",
    },
    {
      section: "assumptions",
      title: "Assumptions / side conditions",
      body: assumps,
      emptyNote: "(none listed — confirm no hidden defaults)",
    },
    {
      section: "epistemicLabel",
      title: "Epistemic state",
      body: epi.label,
      detail: epi.detail,
      allowCertified: epi.allowCertified,
    },
  ];

  return {
    epistemic: epi,
    leanProposition: proposition,
    assumptions: assumps,
    transcript,
    transcriptOrder: transcript.map((t) => t.section),
    certifiedAffordanceIndex: transcript.findIndex(
      (t) => t.section === "epistemicLabel"
    ),
  };
}

module.exports = {
  LEAN_OK_STATUSES,
  leanStatusAllowsCertified,
  epistemicFromResultStatus,
  extractAssumptions,
  extractLeanProposition,
  buildCertificationSurface,
};
