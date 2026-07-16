"""Mathematica / LeanLink adapter package (closed v0 backend)."""

from adapters.mathematica.adapter import (
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
