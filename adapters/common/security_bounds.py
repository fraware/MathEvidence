"""Parser and path security bounds (docs/security/SECURITY_AND_TRUST_MODEL §5–6)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.common.errors import stable_error
from adapters.common.limits import ResourceLimits

DEFAULT_MAX_INTEGER_DIGITS = 4096


def json_nesting_depth(value: Any, *, _depth: int = 0) -> int:
    """Return maximum nesting depth of lists/dicts in a JSON-like value."""
    if isinstance(value, dict):
        if not value:
            return _depth + 1
        return max(json_nesting_depth(v, _depth=_depth + 1) for v in value.values())
    if isinstance(value, list):
        if not value:
            return _depth + 1
        return max(json_nesting_depth(v, _depth=_depth + 1) for v in value)
    return _depth


def enforce_nesting_depth(value: Any, *, limits: ResourceLimits | None = None) -> int:
    """Reject values deeper than ``max_nesting_depth``."""
    lim = limits or ResourceLimits()
    depth = json_nesting_depth(value)
    if depth > lim.max_nesting_depth:
        raise stable_error(
            "resource_limit_exceeded",
            f"JSON nesting depth {depth} exceeds {lim.max_nesting_depth}",
            details={"kind": "nesting_depth", "depth": depth},
        )
    return depth


def integer_digit_count(text: str) -> int:
    """Count decimal digits in an integer string (optional leading sign)."""
    s = text.strip()
    if s.startswith(("+", "-")):
        s = s[1:]
    if not s or not s.isdigit():
        raise stable_error(
            "malformed_evidence",
            f"integer literal is not a decimal digit string: {text!r}",
        )
    return len(s.lstrip("0") or "0")


def enforce_integer_digits(
    text: str,
    *,
    max_digits: int = DEFAULT_MAX_INTEGER_DIGITS,
) -> int:
    digits = integer_digit_count(text)
    if digits > max_digits:
        raise stable_error(
            "resource_limit_exceeded",
            f"integer has {digits} digits; max is {max_digits}",
            details={"kind": "integer_digits", "digits": digits},
        )
    return digits


def walk_enforce_integer_digits(
    value: Any,
    *,
    max_digits: int = DEFAULT_MAX_INTEGER_DIGITS,
) -> None:
    """Walk RationalExpr-shaped JSON and reject oversized int/rat numerals."""
    if isinstance(value, dict):
        tag = value.get("tag")
        if tag == "int":
            enforce_integer_digits(str(value.get("value", "")), max_digits=max_digits)
        elif tag == "rat":
            enforce_integer_digits(str(value.get("num", "")), max_digits=max_digits)
            enforce_integer_digits(str(value.get("den", "")), max_digits=max_digits)
        for v in value.values():
            walk_enforce_integer_digits(v, max_digits=max_digits)
    elif isinstance(value, list):
        for v in value:
            walk_enforce_integer_digits(v, max_digits=max_digits)


def reject_path_traversal(rel: str, *, root: Path | None = None) -> Path | None:
    """Reject ``..`` / absolute paths; optionally resolve under ``root``."""
    normalized = rel.replace("\\", "/")
    parts = normalized.split("/")
    if normalized.startswith("/") or any(p == ".." for p in parts):
        raise stable_error(
            "malformed_evidence",
            f"path traversal rejected: {rel}",
            details={"kind": "path_traversal", "path": rel},
        )
    if root is None:
        return None
    candidate = (root / rel).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise stable_error(
            "malformed_evidence",
            f"path escapes workspace: {rel}",
            details={"kind": "path_traversal", "path": rel},
        ) from exc
    return candidate
