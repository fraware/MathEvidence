"""Mathematica / LeanLink adapter package (closed v0 backend)."""

from adapters.mathematica.adapter import (
    ADAPTER_VERSION,
    RATIONAL_EQUALITY_CAPABILITY,
    certificate_from_wl_payload,
    check_support,
    compute_handler,
    compute_rational_equality,
    discover_runtime,
)

__all__ = [
    "ADAPTER_VERSION",
    "RATIONAL_EQUALITY_CAPABILITY",
    "certificate_from_wl_payload",
    "check_support",
    "compute_handler",
    "compute_rational_equality",
    "discover_runtime",
]
