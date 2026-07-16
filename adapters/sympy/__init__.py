"""SymPy adapter package (open v0 backend)."""

from adapters.sympy.adapter import (
    ADAPTER_VERSION,
    RATIONAL_EQUALITY_CAPABILITY,
    check_support,
    compute_handler,
    compute_rational_equality,
)

__all__ = [
    "ADAPTER_VERSION",
    "RATIONAL_EQUALITY_CAPABILITY",
    "check_support",
    "compute_handler",
    "compute_rational_equality",
]
