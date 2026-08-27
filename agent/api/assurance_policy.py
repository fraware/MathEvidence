"""Registry-backed assurance policy.

Policy embedded in ``registry/capabilities/*.json`` under ``assurancePolicy`` is
the only authority for theorem promotion and exact-candidate fail-closed
decisions. Fixture keys and OfflineFixtures are never CR authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.api.registry_query import find_capability, load_capabilities

REPO_ROOT = Path(__file__).resolve().parents[2]

ASSURANCE_MODE_UNAVAILABLE = "assurance_mode_unavailable"
OUTCOME_PROVED = "proved"
OUTCOME_REFUTED = "refuted"
OUTCOME_EVIDENCE_ONLY = "evidence_only"
ALLOWED_OUTCOMES = frozenset({OUTCOME_PROVED, OUTCOME_REFUTED, OUTCOME_EVIDENCE_ONLY})
NA_SENTINEL = "n/a"

_EXACT_META_KEYS = (
    "generatorId",
    "generatorVersion",
    "grammarVersion",
    "generatorPath",
    "verifier",
)


@dataclass(frozen=True)
class AssuranceDecision:
    """Fail-closed decision for a capability/mode request."""

    ok: bool
    code: str | None
    message: str
    capability_id: str
    policy: dict[str, Any] | None = None


def _policy_from_capability(cap: dict[str, Any] | None) -> dict[str, Any] | None:
    if cap is None:
        return None
    policy = cap.get("assurancePolicy")
    return policy if isinstance(policy, dict) else None


def load_assurance_policy(capability_id: str) -> dict[str, Any] | None:
    """Return embedded assurancePolicy for a capability, or None if unknown."""
    return _policy_from_capability(find_capability(capability_id))


def load_all_assurance_policies() -> dict[str, dict[str, Any]]:
    """Map capability id -> assurancePolicy for every registry entry that has one."""
    out: dict[str, dict[str, Any]] = {}
    for cap in load_capabilities():
        policy = _policy_from_capability(cap)
        if policy is not None:
            out[str(cap["id"])] = policy
    return out


def exact_binding(policy: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(policy, dict):
        return {"supported": False}
    binding = policy.get("exactBinding")
    return binding if isinstance(binding, dict) else {"supported": False}


def exact_binding_supported(capability_id: str) -> bool:
    return exact_binding(load_assurance_policy(capability_id)).get("supported") is True


def cr_eligible(capability_id: str) -> bool:
    policy = load_assurance_policy(capability_id)
    if policy is None:
        return False
    cert = policy.get("certification")
    if not isinstance(cert, dict):
        return False
    return cert.get("crEligible") is True


def allowed_outcomes(capability_id: str) -> frozenset[str]:
    policy = load_assurance_policy(capability_id)
    if policy is None:
        return frozenset()
    cert = policy.get("certification")
    if not isinstance(cert, dict):
        return frozenset()
    values = cert.get("allowedOutcomes") or []
    if not isinstance(values, list):
        return frozenset()
    return frozenset(str(v) for v in values)


def supported_assurance_modes(capability_id: str) -> frozenset[str]:
    policy = load_assurance_policy(capability_id)
    if policy is None:
        return frozenset()
    modes = policy.get("supportedAssuranceModes") or []
    if not isinstance(modes, list):
        return frozenset()
    return frozenset(str(m) for m in modes)


def decide_exact_kernel_replay(capability_id: str) -> AssuranceDecision:
    """Gate for theorem-producing exact kernel replay.

    Unknown capability, missing policy, non-CR-eligible policy, unsupported mode,
    or unsupported exact binding => ``assurance_mode_unavailable``. Never falls
    back to fixtures.
    """
    cap = find_capability(capability_id)
    if cap is None:
        return AssuranceDecision(
            ok=False,
            code=ASSURANCE_MODE_UNAVAILABLE,
            message=f"unknown capability: {capability_id}",
            capability_id=capability_id,
        )
    policy = _policy_from_capability(cap)
    if policy is None:
        return AssuranceDecision(
            ok=False,
            code=ASSURANCE_MODE_UNAVAILABLE,
            message=f"capability {capability_id} has no assurancePolicy",
            capability_id=capability_id,
        )
    if not cr_eligible(capability_id):
        return AssuranceDecision(
            ok=False,
            code=ASSURANCE_MODE_UNAVAILABLE,
            message=(
                f"theorem Certification Record replay is not enabled for {capability_id}; "
                "registry certification.crEligible must be true"
            ),
            capability_id=capability_id,
            policy=policy,
        )
    modes = supported_assurance_modes(capability_id)
    if "kernel_replay" not in modes:
        return AssuranceDecision(
            ok=False,
            code=ASSURANCE_MODE_UNAVAILABLE,
            message=f"kernel_replay is not a supported assurance mode for {capability_id}",
            capability_id=capability_id,
            policy=policy,
        )
    binding = exact_binding(policy)
    if binding.get("supported") is not True:
        return AssuranceDecision(
            ok=False,
            code=ASSURANCE_MODE_UNAVAILABLE,
            message=(
                "generic Certification Record replay is disabled for this capability until "
                "an exact-candidate generator replaces OfflineFixtures substitution"
            ),
            capability_id=capability_id,
            policy=policy,
        )
    missing = [key for key in _EXACT_META_KEYS if not binding.get(key)]
    if missing:
        return AssuranceDecision(
            ok=False,
            code=ASSURANCE_MODE_UNAVAILABLE,
            message=f"exactBinding metadata incomplete: missing {missing}",
            capability_id=capability_id,
            policy=policy,
        )
    return AssuranceDecision(
        ok=True,
        code=None,
        message="exact kernel replay allowed by registry policy",
        capability_id=capability_id,
        policy=policy,
    )


def outcome_allowed(capability_id: str, outcome: str) -> bool:
    allowed = allowed_outcomes(capability_id)
    if not allowed:
        # Conservative default: empty allowedOutcomes forbids theorem polarity minting.
        return False
    return outcome in allowed


def map_claim_to_outcome(*, claim_class: str, claim_established: str | None) -> str:
    """Map protocol claim class to CR outcome polarity."""
    if claim_class == "refutation" and isinstance(claim_established, str) and claim_established:
        return OUTCOME_REFUTED
    if claim_established in {"witness", "soundResult", "completeSolution", "optimum"}:
        return OUTCOME_PROVED
    return OUTCOME_EVIDENCE_ONLY


def validate_assurance_policy_object(
    policy: dict[str, Any],
    *,
    capability_id: str,
    repo_root: Path = REPO_ROOT,
) -> list[str]:
    """Structural policy rules beyond JSON Schema (used by validate_registry)."""
    errors: list[str] = []
    binding = exact_binding(policy)
    supported = binding.get("supported") is True
    maturity = policy.get("maturity") if isinstance(policy.get("maturity"), dict) else {}
    exact_exists = maturity.get("exactCandidateBindingExists") is True
    cert = policy.get("certification") if isinstance(policy.get("certification"), dict) else {}
    cr = cert.get("crEligible") is True
    modes = policy.get("supportedAssuranceModes")
    if not isinstance(modes, list):
        errors.append(f"{capability_id}: supportedAssuranceModes must be an array")
        modes = []

    if exact_exists != supported:
        errors.append(
            f"{capability_id}: maturity.exactCandidateBindingExists={exact_exists} "
            f"disagrees with exactBinding.supported={supported}"
        )

    if supported:
        missing = [key for key in _EXACT_META_KEYS if not binding.get(key)]
        if missing:
            errors.append(
                f"{capability_id}: exactBinding.supported requires fields {missing}"
            )
        gen_path = binding.get("generatorPath")
        if isinstance(gen_path, str) and gen_path:
            target = repo_root / gen_path
            if not target.is_file():
                errors.append(
                    f"{capability_id}: exactBinding.generatorPath missing: {gen_path}"
                )
        if "kernel_replay" not in modes:
            errors.append(
                f"{capability_id}: exactBinding.supported requires kernel_replay "
                "in supportedAssuranceModes"
            )

    if cr:
        if not supported:
            errors.append(
                f"{capability_id}: certification.crEligible=true requires exactBinding.supported"
            )
        missing = [key for key in _EXACT_META_KEYS if not binding.get(key)]
        if missing:
            errors.append(
                f"{capability_id}: crEligible=true requires exactBinding fields {missing}"
            )
        verifier = binding.get("verifier")
        if not isinstance(verifier, str) or not verifier.strip():
            errors.append(f"{capability_id}: crEligible=true requires exactBinding.verifier")

    outcomes = cert.get("allowedOutcomes")
    if isinstance(outcomes, list):
        for outcome in outcomes:
            if outcome not in ALLOWED_OUTCOMES:
                errors.append(f"{capability_id}: unknown allowedOutcome {outcome!r}")

    for mode in modes:
        if mode not in {"kernel_replay", "verified_reflection", "native_checked"}:
            errors.append(f"{capability_id}: unknown assurance mode {mode!r}")

    return errors


def historical_exact_replay_capabilities() -> frozenset[str]:
    """Exact-binding capability set used for differential tests."""
    return frozenset(
        {
            "algebra.ideal_membership_witness",
            "algebra.rational_equality",
            "algebra.linear_algebra",
            "logic.finite_counterexample",
            "algebra.formal_rational_calculus",
            "analysis.analytic_calculus",
        }
    )
