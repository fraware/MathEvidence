"""Agent API operation catalog (no arbitrary shell)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PROTOCOL_VERSION = "0.1.0"

ALLOWED_BACKENDS = frozenset({"sympy", "mathematica", "sage"})


@dataclass(frozen=True)
class OperationDescriptor:
    id: str
    summary: str
    input_schema: str
    output_schema: str
    claim_classes: list[str]
    max_resource_policy: dict[str, int]
    notes: list[str] = field(default_factory=list)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "inputSchema": self.input_schema,
            "outputSchema": self.output_schema,
            "claimClasses": self.claim_classes,
            "maxResourcePolicy": self.max_resource_policy,
            "notes": list(self.notes),
        }


_BASE = "agent/api/schemas/"
_RESULT = f"{_BASE}agent-result.schema.json"

OPERATIONS: dict[str, OperationDescriptor] = {
    "list_capabilities": OperationDescriptor(
        id="list_capabilities",
        summary="Discover versioned capability declarations from the registry",
        input_schema=f"{_BASE}list-capabilities.input.schema.json",
        output_schema=f"{_BASE}list-capabilities.output.schema.json",
        claim_classes=["discovery"],
        max_resource_policy={"maxWallTimeMs": 5000, "maxOutputBytes": 1_048_576},
        notes=["Reads registry JSON only; does not invoke solvers."],
    ),
    "check_support": OperationDescriptor(
        id="check_support",
        summary="Reject unsupported capability/backend/claim combinations before compute",
        input_schema=f"{_BASE}check-support.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["discovery"],
        max_resource_policy={"maxWallTimeMs": 5000, "maxOutputBytes": 65_536},
    ),
    "compute_evidence": OperationDescriptor(
        id="compute_evidence",
        summary="Run a named adapter compute for a registered capability",
        input_schema=f"{_BASE}compute-evidence.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["candidate", "soundResult", "witness"],
        max_resource_policy={"maxWallTimeMs": 60_000, "maxOutputBytes": 4_194_304},
        notes=[
            "Returns resultStatus computed|rejected|unsupported|ambiguous at most.",
            "Never marks soundness_verified; Lean checkers own certification.",
            "Backend must be one of: sympy, mathematica, sage.",
        ],
    ),
    "open_bundle": OperationDescriptor(
        id="open_bundle",
        summary="Open an EvidenceBundle and surface epistemic resultStatus",
        input_schema=f"{_BASE}open-bundle.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["replay"],
        max_resource_policy={"maxWallTimeMs": 10_000, "maxOutputBytes": 1_048_576},
    ),
    "replay_bundle": OperationDescriptor(
        id="replay_bundle",
        summary="Offline schema and digest verification of an EvidenceBundle",
        input_schema=f"{_BASE}replay-bundle.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["replay"],
        max_resource_policy={"maxWallTimeMs": 30_000, "maxOutputBytes": 1_048_576},
        notes=["Python offline replay only; Lean kernel replay is separate."],
    ),
    "propose_conditions": OperationDescriptor(
        id="propose_conditions",
        summary="Propose side conditions from a backend / IR heuristics (untrusted)",
        input_schema=f"{_BASE}hypothesis.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["candidate"],
        max_resource_policy={"maxWallTimeMs": 30_000, "maxOutputBytes": 1_048_576},
        notes=["Never silently inserted into theorems."],
    ),
    "prove_sufficient": OperationDescriptor(
        id="prove_sufficient",
        summary="Sufficiency via Lean RationalEquality.checkBool mirror only",
        input_schema=f"{_BASE}hypothesis.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["candidate"],
        max_resource_policy={"maxWallTimeMs": 30_000, "maxOutputBytes": 1_048_576},
        notes=[
            "authorityStatus=lean_checker_mirror; kernel replay remains final.",
            "Heuristics/polyZeroHint never determine acceptance.",
        ],
    ),
    "delete_hypothesis": OperationDescriptor(
        id="delete_hypothesis",
        summary="Hypothesis deletion with redundancy via Lean checkBool mirror",
        input_schema=f"{_BASE}hypothesis.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["candidate"],
        max_resource_policy={"maxWallTimeMs": 30_000, "maxOutputBytes": 1_048_576},
        notes=["authorityStatus=lean_checker_mirror; absence of CEX is not necessity."],
    ),
    "find_counterexample": OperationDescriptor(
        id="find_counterexample",
        summary="Bounded search for a finite counterexample witness (untrusted)",
        input_schema=f"{_BASE}hypothesis.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["witness", "refutation"],
        max_resource_policy={"maxWallTimeMs": 60_000, "maxOutputBytes": 1_048_576},
    ),
    "verify_counterexample": OperationDescriptor(
        id="verify_counterexample",
        summary="Verify finite CEX via Lean Counterexample.checkBool mirror",
        input_schema=f"{_BASE}hypothesis.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["witness", "refutation"],
        max_resource_policy={"maxWallTimeMs": 30_000, "maxOutputBytes": 1_048_576},
        notes=["authorityStatus=lean_checker_mirror; kernel replay remains final."],
    ),
    "build_condition_lattice": OperationDescriptor(
        id="build_condition_lattice",
        summary="Build condition lattice via Lean-authoritative sufficiency/deletion/CEX",
        input_schema=f"{_BASE}hypothesis.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["candidate"],
        max_resource_policy={"maxWallTimeMs": 60_000, "maxOutputBytes": 2_097_152},
        notes=[
            "authorityStatus=lean_checker_mirror on sufficiency/deletion/CEX fields.",
            "Minimality never claimed by default; expert review required.",
        ],
    ),
    "conjecture_campaign": OperationDescriptor(
        id="conjecture_campaign",
        summary="Run a conjecture episode: candidate vs certified refutation only",
        input_schema=f"{_BASE}hypothesis.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["candidate", "refutation"],
        max_resource_policy={"maxWallTimeMs": 60_000, "maxOutputBytes": 2_097_152},
        notes=["Bounded verification is never an unbounded theorem."],
    ),
    "inspect_bundle": OperationDescriptor(
        id="inspect_bundle",
        summary="Alias of open_bundle — summarize an EvidenceBundle without closing goals",
        input_schema=f"{_BASE}open-bundle.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["replay"],
        max_resource_policy={"maxWallTimeMs": 10_000, "maxOutputBytes": 1_048_576},
        notes=["Same handler as open_bundle; public path fields are rejected."],
    ),
    "build_proof_plan": OperationDescriptor(
        id="build_proof_plan",
        summary="Trace-to-Plan build; Agent returns unsupported without Lean receipt",
        input_schema=f"{_BASE}ttp.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["candidate"],
        max_resource_policy={"maxWallTimeMs": 30_000, "maxOutputBytes": 1_048_576},
        notes=[
            "Honestly unsupported on the Python Agent surface.",
            "Use Lean TraceToPlan / committed receipts; Agent never upgrades to verified.",
        ],
    ),
    "reconstruct_plan": OperationDescriptor(
        id="reconstruct_plan",
        summary="Trace-to-Plan reconstruct; Agent returns unsupported without receipt",
        input_schema=f"{_BASE}ttp.input.schema.json",
        output_schema=_RESULT,
        claim_classes=["candidate"],
        max_resource_policy={"maxWallTimeMs": 30_000, "maxOutputBytes": 1_048_576},
        notes=[
            "Honestly unsupported on the Python Agent surface without a Lean receipt.",
            "Hint-only reconstruct must not advance plan state.",
        ],
    ),
}


def list_operations() -> list[dict[str, Any]]:
    return [op.to_public() for op in OPERATIONS.values()]
