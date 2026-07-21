"""Deterministic checker-receipt canonicalization, content digest, and optional
dev-only HMAC / Ed25519 signing.

This is **not** production PKI. Keys generated under ``dev/receipt-keys/`` are for
local Agent/Studio verification experiments only.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

from adapters.common.canonical import canonical_dumps, sha256_digest

# Fields excluded from the binding payload (derived / signature envelope).
_RECEIPT_NON_BINDING = frozenset(
    {
        "receiptDigest",
        "contentDigest",
        "signature",
        "signatureAlg",
        "signatureKeyId",
    }
)

DEV_KEY_DIR_ENV = "MATHEVIDENCE_RECEIPT_KEY_DIR"


def receipt_binding_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    """Return receipt fields that participate in content digest / signatures."""
    return {k: v for k, v in receipt.items() if k not in _RECEIPT_NON_BINDING}


def canonicalize_receipt(receipt: dict[str, Any]) -> str:
    """Canonical JSON text of the binding payload (UTF-8, no whitespace)."""
    return canonical_dumps(receipt_binding_payload(receipt))


def receipt_content_digest(receipt: dict[str, Any]) -> str:
    """SHA-256 digest of canonical receipt bytes as ``sha256:<hex>``."""
    return sha256_digest(receipt_binding_payload(receipt))


def attach_receipt_digest(receipt: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with ``receiptDigest`` / ``contentDigest`` set identically."""
    out = dict(receipt)
    digest = receipt_content_digest(out)
    out["receiptDigest"] = digest
    out["contentDigest"] = digest
    return out


def verify_receipt_digest(receipt: dict[str, Any]) -> str:
    """Verify ``receiptDigest`` (or ``contentDigest``) matches canonical bytes."""
    expected = receipt_content_digest(receipt)
    declared = receipt.get("receiptDigest") or receipt.get("contentDigest")
    if not isinstance(declared, str) or not declared.startswith("sha256:"):
        raise ValueError("receiptDigest/contentDigest missing or malformed")
    if declared != expected:
        raise ValueError(
            f"receipt content digest mismatch: got {declared}, expected {expected}"
        )
    return expected


def default_dev_key_dir(repo_root: Path | None = None) -> Path:
    env = os.environ.get(DEV_KEY_DIR_ENV)
    if env:
        return Path(env)
    root = repo_root or Path(__file__).resolve().parents[2]
    return root / "dev" / "receipt-keys"


def ensure_dev_hmac_key(key_dir: Path | None = None) -> Path:
    """Create a deterministic-path HMAC key for local dev if absent."""
    key_dir = key_dir or default_dev_key_dir()
    key_dir.mkdir(parents=True, exist_ok=True)
    readme = key_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Dev-only receipt keys\n\n"
            "These keys are for **local development** HMAC/Ed25519 experiments.\n"
            "They are **not** production PKI and must not be used to assert\n"
            "release integrity or stable-promotion trust.\n",
            encoding="utf-8",
        )
    path = key_dir / "hmac-dev.key"
    if not path.exists():
        path.write_bytes(os.urandom(32))
    return path


def ensure_dev_ed25519_keypair(key_dir: Path | None = None) -> tuple[Path, Path]:
    """Create a local Ed25519 keypair for dev signing if cryptography is available."""
    key_dir = key_dir or default_dev_key_dir()
    key_dir.mkdir(parents=True, exist_ok=True)
    priv_path = key_dir / "ed25519-dev.pem"
    pub_path = key_dir / "ed25519-dev.pub.pem"
    if priv_path.exists() and pub_path.exists():
        return priv_path, pub_path
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "cryptography package required for Ed25519 receipt signing"
        ) from exc
    key = Ed25519PrivateKey.generate()
    priv_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    pub_path.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return priv_path, pub_path


def sign_receipt_hmac(
    receipt: dict[str, Any], *, key: bytes, key_id: str = "hmac-dev"
) -> dict[str, Any]:
    """Attach HMAC-SHA256 over canonical receipt bytes (dev only)."""
    out = attach_receipt_digest(receipt)
    body = canonicalize_receipt(out).encode("utf-8")
    sig = hmac.new(key, body, hashlib.sha256).hexdigest()
    out["signatureAlg"] = "hmac-sha256"
    out["signatureKeyId"] = key_id
    out["signature"] = "hex:" + sig
    return out


def verify_receipt_hmac(
    receipt: dict[str, Any], *, key: bytes, key_id: str | None = None
) -> bool:
    """Verify HMAC when ``signatureAlg`` is ``hmac-sha256``."""
    if receipt.get("signatureAlg") != "hmac-sha256":
        return False
    if key_id is not None and receipt.get("signatureKeyId") != key_id:
        return False
    verify_receipt_digest(receipt)
    body = canonicalize_receipt(receipt).encode("utf-8")
    expected = "hex:" + hmac.new(key, body, hashlib.sha256).hexdigest()
    sig = receipt.get("signature")
    return isinstance(sig, str) and hmac.compare_digest(sig, expected)


def sign_receipt_ed25519(
    receipt: dict[str, Any],
    *,
    private_key_pem: bytes,
    key_id: str = "ed25519-dev",
) -> dict[str, Any]:
    """Attach Ed25519 signature over canonical receipt bytes (dev only)."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = serialization.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("expected Ed25519 private key")
    out = attach_receipt_digest(receipt)
    body = canonicalize_receipt(out).encode("utf-8")
    sig = key.sign(body)
    out["signatureAlg"] = "ed25519"
    out["signatureKeyId"] = key_id
    out["signature"] = "hex:" + sig.hex()
    return out


def verify_receipt_ed25519(
    receipt: dict[str, Any], *, public_key_pem: bytes, key_id: str | None = None
) -> bool:
    """Verify Ed25519 when ``signatureAlg`` is ``ed25519``."""
    if receipt.get("signatureAlg") != "ed25519":
        return False
    if key_id is not None and receipt.get("signatureKeyId") != key_id:
        return False
    verify_receipt_digest(receipt)
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    key = serialization.load_pem_public_key(public_key_pem)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("expected Ed25519 public key")
    sig = receipt.get("signature")
    if not isinstance(sig, str) or not sig.startswith("hex:"):
        return False
    body = canonicalize_receipt(receipt).encode("utf-8")
    try:
        key.verify(bytes.fromhex(sig[4:]), body)
        return True
    except Exception:
        return False


def verify_receipt_signature_if_present(
    receipt: dict[str, Any],
    *,
    key_dir: Path | None = None,
) -> dict[str, Any]:
    """Verify digest always; verify signature when present and keys are available.

    Returns a gate dict compatible with Studio/Agent receipt checks.
    """
    try:
        digest = verify_receipt_digest(receipt)
    except ValueError as exc:
        return {
            "ok": False,
            "digestVerified": False,
            "signatureVerified": False,
            "detail": str(exc),
        }

    alg = receipt.get("signatureAlg")
    if alg is None:
        return {
            "ok": True,
            "digestVerified": True,
            "signatureVerified": False,
            "signatureStatus": "unsigned",
            "detail": f"content digest ok ({digest}); unsigned receipt",
        }

    key_dir = key_dir or default_dev_key_dir()
    if alg == "hmac-sha256":
        key_path = key_dir / "hmac-dev.key"
        if not key_path.is_file():
            return {
                "ok": False,
                "digestVerified": True,
                "signatureVerified": False,
                "detail": "HMAC signature present but hmac-dev.key missing",
            }
        ok = verify_receipt_hmac(receipt, key=key_path.read_bytes())
        return {
            "ok": ok,
            "digestVerified": True,
            "signatureVerified": ok,
            "signatureStatus": "hmac-sha256",
            "detail": "HMAC verified" if ok else "HMAC verification failed",
        }
    if alg == "ed25519":
        pub_path = key_dir / "ed25519-dev.pub.pem"
        if not pub_path.is_file():
            return {
                "ok": False,
                "digestVerified": True,
                "signatureVerified": False,
                "detail": "Ed25519 signature present but public key missing",
            }
        ok = verify_receipt_ed25519(receipt, public_key_pem=pub_path.read_bytes())
        return {
            "ok": ok,
            "digestVerified": True,
            "signatureVerified": ok,
            "signatureStatus": "ed25519",
            "detail": "Ed25519 verified" if ok else "Ed25519 verification failed",
        }
    return {
        "ok": False,
        "digestVerified": True,
        "signatureVerified": False,
        "detail": f"unsupported signatureAlg {alg!r}",
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
