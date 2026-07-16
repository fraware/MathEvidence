"""SageMath adapter package (optional third open backend)."""

from adapters.sage.adapter import (
    ADAPTER_VERSION,
    RATIONAL_EQUALITY_CAPABILITY,
    check_support,
    compute_handler,
    compute_rational_equality,
    discover_runtime,
)

__all__ = [
    "ADAPTER_VERSION",
    "RATIONAL_EQUALITY_CAPABILITY",
    "check_support",
    "compute_handler",
    "compute_rational_equality",
    "discover_runtime",
]
