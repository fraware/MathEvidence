"""Shared product epistemic states (Wave 6 / ME-RV-060..062).

Only ``kernel_certified`` carries a theorem or refutation claim.
Python checker mirrors may report ``mirror_accepted`` only.
"""

from __future__ import annotations

from typing import Final

# Normative shared vocabulary from
# docs/audits/2026-07-26-real-vision/09_HYPOTHESIS_CONJECTURE_TRACE_TO_PLAN.md
PRODUCT_STATES: Final[tuple[str, ...]] = (
    "proposed",
    "mirror_accepted",
    "checker_accepted",
    "kernel_certified",
    "rejected",
    "unknown",
)

PRODUCT_STATE_SET: Final[frozenset[str]] = frozenset(PRODUCT_STATES)

# Authority labels for Agent-side mirrors vs kernel.
AUTHORITY_PYTHON_MIRROR: Final[str] = "python_checker_mirror"
AUTHORITY_LEAN_KERNEL: Final[str] = "lean_kernel"

# Backward-compat alias used by older callers/tests.
AUTHORITY_LEAN_CHECKER_MIRROR: Final[str] = AUTHORITY_PYTHON_MIRROR


def is_proof_bearing(state: str | None) -> bool:
    """True only for states that may assert a theorem or refutation claim."""
    return state == "kernel_certified"


def normalize_product_state(value: str | None, *, default: str = "unknown") -> str:
    if isinstance(value, str) and value in PRODUCT_STATE_SET:
        return value
    return default
