"""Canonical JSON profile for digest binding (docs/architecture/canonical-json.md).

Profile version: mathevidence-jcs-0.2
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

CANONICALIZATION_PROFILE = "mathevidence-jcs-0.2"


class CanonicalJsonError(ValueError):
    """Raised when a value cannot be canonically serialized for digests."""


def reject_duplicate_keys(text: str) -> Any:
    """Parse JSON text, rejecting duplicate object keys (strict mode)."""

    def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise CanonicalJsonError(f"duplicate JSON key: {key!r}")
            out[key] = value
        return out

    return json.loads(text, object_pairs_hook=_object_pairs)


def _utf16_key_units(key: str) -> list[int]:
    """RFC 8785 key ordering uses UTF-16 code units."""
    units: list[int] = []
    for ch in key:
        cp = ord(ch)
        if cp <= 0xFFFF:
            units.append(cp)
        else:
            cp -= 0x10000
            units.append(0xD800 + (cp >> 10))
            units.append(0xDC00 + (cp & 0x3FF))
    return units


def _escape_string(s: str) -> str:
    """Escape a string per RFC 8785 §3.2.2.2 (subset used by this profile)."""
    parts: list[str] = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"':
            parts.append('\\"')
        elif ch == "\\":
            parts.append("\\\\")
        elif ch == "\b":
            parts.append("\\b")
        elif ch == "\t":
            parts.append("\\t")
        elif ch == "\n":
            parts.append("\\n")
        elif ch == "\f":
            parts.append("\\f")
        elif ch == "\r":
            parts.append("\\r")
        elif o < 0x20:
            parts.append(f"\\u{o:04x}")
        else:
            parts.append(ch)
    parts.append('"')
    return "".join(parts)


def _canonical_number(n: int | float) -> str:
    if isinstance(n, bool):
        raise CanonicalJsonError("booleans must not be serialized as numbers")
    if isinstance(n, float):
        if not math.isfinite(n):
            raise CanonicalJsonError("non-finite floats are forbidden in digests")
        # v0 rational-equality digests forbid floats; reject early.
        raise CanonicalJsonError("floats are forbidden in theorem-binding digests for v0")
    if not isinstance(n, int):
        raise CanonicalJsonError(f"unsupported number type: {type(n)!r}")
    return str(n)


def canonical_dumps(value: Any) -> str:
    """Serialize ``value`` to canonical JSON text (UTF-8, no whitespace)."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _escape_string(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _canonical_number(value)
    if isinstance(value, list):
        return "[" + ",".join(canonical_dumps(v) for v in value) + "]"
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda kv: _utf16_key_units(kv[0]))
        body = ",".join(f"{_escape_string(k)}:{canonical_dumps(v)}" for k, v in items)
        return "{" + body + "}"
    raise CanonicalJsonError(f"unsupported JSON type: {type(value)!r}")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_digest(value: Any, *, prefix: str = "sha256:") -> str:
    """SHA-256 over canonical UTF-8 bytes; returned as ``sha256:<hex>``."""
    text = canonical_dumps(value)
    return prefix + sha256_hex(text.encode("utf-8"))


def request_binding_payload(request: dict[str, Any]) -> dict[str, Any]:
    """Return request fields that participate in digest binding (exclude digest)."""
    return {k: v for k, v in request.items() if k != "requestDigest"}


def bind_request_digest(request: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``request`` with ``requestDigest`` set from payload."""
    payload = request_binding_payload(request)
    out = dict(request)
    out["requestDigest"] = sha256_digest(payload)
    return out


def verify_request_digest(request: dict[str, Any]) -> str:
    """Verify ``requestDigest`` matches the canonical payload; return digest."""
    digest = request.get("requestDigest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise CanonicalJsonError("missing or invalid requestDigest")
    expected = sha256_digest(request_binding_payload(request))
    if digest != expected:
        raise CanonicalJsonError(
            f"requestDigest mismatch: got {digest}, expected {expected}"
        )
    return digest
