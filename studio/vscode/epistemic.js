"use strict";

/**
 * Map ResultStatus / manifest fields to Product 09 epistemic UI states.
 * Color alone is insufficient — always pair with text.
 *
 * HARD RULE (Milestone 5 / Product 09): never present Certified without Lean status.
 *
 * @param {string|undefined} resultStatus
 * @param {string|undefined|null} leanStatus
 * @returns {{ label: "Computed"|"Tested"|"Certified"|"Ambiguous", detail: string }}
 */
function epistemicFromResultStatus(resultStatus, leanStatus) {
  const s = (resultStatus || "").toLowerCase();
  const lean = (leanStatus || "").toLowerCase();
  const leanOk = [
    "soundness_verified",
    "witness_verified",
    "completeness_verified",
    "optimality_verified",
    "approximation_certified",
    "native_verified",
  ].includes(lean);

  if (leanOk) {
    return {
      label: "Certified",
      detail: `Lean status present: ${leanStatus}.`,
    };
  }

  if (
    s === "soundness_verified" ||
    s === "witness_verified" ||
    s === "completeness_verified" ||
    s === "optimality_verified" ||
    s === "approximation_certified" ||
    s === "native_verified"
  ) {
    return {
      label: "Ambiguous",
      detail:
        "Manifest claims a verified status, but Lean status is missing. Not labeled Certified.",
    };
  }
  if (s === "tested") {
    return {
      label: "Tested",
      detail: "Offline schema/digest checks succeeded; Lean certification not asserted.",
    };
  }
  if (s === "computed") {
    return {
      label: "Computed",
      detail: "Backend/candidate output only. Not Lean-certified.",
    };
  }
  if (s === "ambiguous" || s === "rejected" || s === "unsupported" || !s) {
    return {
      label: "Ambiguous",
      detail: "Status is ambiguous, rejected, unsupported, or missing.",
    };
  }
  return {
    label: "Ambiguous",
    detail: `Unrecognized resultStatus: ${resultStatus}`,
  };
}

module.exports = { epistemicFromResultStatus };
