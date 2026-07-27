"use strict";

/**
 * Map ResultStatus / Agent certification fields to Product 09 epistemic UI states.
 *
 * HARD RULE (Wave 2 / ME-RV-024): Certified only when Agent returns
 * certificationVerified + certificationId + claimEstablished + theoremTypeDigest.
 * Never from leanStatus or a raw receipt alone.
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
 * @param {object} opts
 * @returns {{ label: string, detail: string, allowCertified: boolean }}
 */
function certificationGate(opts = {}) {
  const {
    certificationVerified,
    certificationId,
    claimEstablished,
    theoremTypeDigest,
    resultStatus,
  } = opts;
  const verified = certificationVerified === true;
  const certIdOk =
    typeof certificationId === "string" && certificationId.trim().length > 0;
  const claimOk =
    typeof claimEstablished === "string" && claimEstablished.trim().length > 0;
  const theoremOk =
    typeof theoremTypeDigest === "string" &&
    theoremTypeDigest.startsWith("sha256:");
  const status = (resultStatus || "").toLowerCase();
  const statusOk = !status || LEAN_OK_STATUSES.includes(status);

  if (verified && certIdOk && claimOk && theoremOk && statusOk) {
    return {
      label: "Certified",
      detail: `Certification Record verified (${certificationId}); claimEstablished=${claimEstablished}.`,
      allowCertified: true,
    };
  }
  const missing = [];
  if (!verified) missing.push("certificationVerified");
  if (!certIdOk) missing.push("certificationId");
  if (!claimOk) missing.push("claimEstablished");
  if (!theoremOk) missing.push("theoremTypeDigest");
  return {
    label: LEAN_OK_STATUSES.includes(status) ? "Ambiguous" : "Tested",
    detail:
      "Certified requires Agent certificationVerified + certificationId + claimEstablished + theoremTypeDigest (missing: " +
      (missing.join(", ") || "none") +
      ").",
    allowCertified: false,
  };
}

/**
 * @param {string|undefined} resultStatus
 * @param {string|undefined|null} leanStatus
 * @param {object} [certFields]
 * @returns {{ label: "Computed"|"Tested"|"Certified"|"Ambiguous", detail: string, allowCertified: boolean }}
 */
function epistemicFromResultStatus(resultStatus, leanStatus, certFields) {
  const fields = certFields || {};
  const hasCertField =
    (fields.certificationVerified !== undefined &&
      fields.certificationVerified !== null) ||
    (typeof fields.certificationId === "string" && fields.certificationId) ||
    (typeof fields.theoremTypeDigest === "string" && fields.theoremTypeDigest);
  if (hasCertField) {
    return certificationGate({
      certificationVerified: fields.certificationVerified,
      certificationId: fields.certificationId,
      claimEstablished: fields.claimEstablished,
      theoremTypeDigest: fields.theoremTypeDigest,
      resultStatus: resultStatus || leanStatus,
    });
  }

  const s = (resultStatus || "").toLowerCase();

  if (leanStatusAllowsCertified(leanStatus) || LEAN_OK_STATUSES.includes(s)) {
    return {
      label: "Ambiguous",
      detail:
        "Manifest/Lean status alone is insufficient for Certified; open_certification must return certificationVerified=true.",
      allowCertified: false,
    };
  }
  if (s === "tested" || s === "checker_accepted") {
    return {
      label: "Tested",
      detail:
        "Offline schema/digest checks and/or operational checkBool succeeded; theorem Certified requires a Certification Record (not verify-bundle).",
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
  const { leanProposition, theoremPreview, request, manifest } = opts;
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
    certificationVerified,
    certificationId,
    claimEstablished,
    theoremTypeDigest,
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

  let epi = epistemicFromResultStatus(resultStatus, leanStatus, {
    certificationVerified,
    certificationId,
    claimEstablished,
    theoremTypeDigest,
  });
  if (epi.allowCertified && !proposition) {
    epi = {
      label: "Ambiguous",
      detail:
        "Certification Record is present, but the exact Lean proposition is not available yet. Not labeled Certified.",
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
    certificationVerified: certificationVerified === true,
  };
}

module.exports = {
  LEAN_OK_STATUSES,
  leanStatusAllowsCertified,
  certificationGate,
  epistemicFromResultStatus,
  extractAssumptions,
  extractLeanProposition,
  buildCertificationSurface,
};
