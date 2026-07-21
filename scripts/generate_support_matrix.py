#!/usr/bin/env python3
"""Generate a support matrix from registry + conformance evidence.

Registry capability files declare supportClaims. This script never elevates a
claim above on-disk evidence:

- ``conformanceVerified`` requires ``conformance.status == passing`` AND the
  suite path to exist with at least one case/bundle artifact.
- Backend ``supportLevel`` is capped to what the capability file already
  declares; this generator records evidence pointers, it does not invent live
  probes.

Output: ``registry/support-matrix.json``.

Signing:
- Default: unsigned envelope with ``signatureStatus: unsigned`` and a
  deterministic ``matrixDigest`` / ``contentDigest`` over the canonical body.
- Optional ``--sign-hmac``: attach a **dev-only** HMAC over the canonical body
  using ``dev/receipt-keys/hmac-dev.key`` (not production PKI).
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.common.canonical import canonical_dumps  # noqa: E402
from adapters.common.receipt_crypto import (  # noqa: E402
    default_dev_key_dir,
    ensure_dev_hmac_key,
)

CAPS_DIR = ROOT / "registry" / "capabilities"
OUT_DEFAULT = ROOT / "registry" / "support-matrix.json"

_NON_BINDING = frozenset(
    {"matrixDigest", "contentDigest", "signature", "signatureAlg", "signatureKeyId"}
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return "sha256:" + h.hexdigest()


def _suite_exists(suite: str) -> tuple[bool, int]:
    path = ROOT / suite
    if not path.exists():
        return False, 0
    if path.is_file():
        return True, 1
    count = 0
    for pattern in ("**/case.json", "**/bundle/manifest.json", "**/*.lean"):
        count += len(list(path.glob(pattern)))
    return True, count


def _row_for_capability(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    support = data.get("supportClaims") or {}
    conformance = data.get("conformance") or {}
    suite = str(conformance.get("suite") or "")
    suite_ok, artifact_count = _suite_exists(suite) if suite else (False, 0)
    declared_verified = bool(support.get("conformanceVerified"))
    status = conformance.get("status")
    evidence_verified = (
        declared_verified and status == "passing" and suite_ok and artifact_count > 0
    )
    backends = []
    for b in support.get("backends") or []:
        if not isinstance(b, dict):
            continue
        level = b.get("supportLevel") or "declared"
        if level == "conformance_verified" and not evidence_verified:
            level = "implemented"
        backends.append(
            {
                "id": b.get("id"),
                "versions": b.get("versions") or [],
                "supportLevel": level,
                "evidenceCapped": level != (b.get("supportLevel") or "declared"),
            }
        )
    return {
        "id": data.get("id"),
        "version": data.get("version"),
        "lifecycle": data.get("lifecycle") or data.get("status"),
        "implementationLevel": data.get("implementationLevel"),
        "adoptionLevel": data.get("adoptionLevel"),
        "federationLevel": data.get("federationLevel"),
        "semanticReview": data.get("semanticReview", "absent"),
        "trustReview": data.get("trustReview", "absent"),
        "externalSearchEssential": data.get("externalSearchEssential"),
        "conformance": {
            "suite": suite,
            "status": status,
            "suiteExists": suite_ok,
            "artifactCount": artifact_count,
            "requiredCases": conformance.get("requiredCases") or [],
        },
        "supportClaims": {
            "declared": bool(support.get("declared")),
            "conformanceVerifiedDeclared": declared_verified,
            "conformanceVerifiedEvidence": evidence_verified,
            "installedHint": support.get("installedHint"),
            "backends": backends,
        },
        "descriptorDigest": _sha256_file(path),
        "descriptorPath": str(path.relative_to(ROOT)).replace("\\", "/"),
    }


def _binding_payload(matrix: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in matrix.items() if k not in _NON_BINDING}


def _attach_content_digest(matrix: dict[str, Any]) -> dict[str, Any]:
    body = canonical_dumps(_binding_payload(matrix)).encode("utf-8")
    digest = "sha256:" + hashlib.sha256(body).hexdigest()
    out = dict(matrix)
    out["matrixDigest"] = digest
    out["contentDigest"] = digest
    return out


def generate(*, sign_hmac: bool = False) -> dict[str, Any]:
    rows = []
    for path in sorted(CAPS_DIR.glob("*.json")):
        rows.append(_row_for_capability(path))
    payload: dict[str, Any] = {
        "schemaVersion": "0.1.0",
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/generate_support_matrix.py",
        "signatureStatus": "unsigned",
        "signatureNote": (
            "Default output is intentionally unsigned. "
            "``matrixDigest``/``contentDigest`` bind the canonical unsigned body. "
            "Optional ``--sign-hmac`` attaches a **dev-only** HMAC (not production PKI)."
        ),
        "capabilities": rows,
    }
    payload = _attach_content_digest(payload)
    if sign_hmac:
        key_path = ensure_dev_hmac_key(default_dev_key_dir(ROOT))
        body = canonical_dumps(_binding_payload(payload)).encode("utf-8")
        sig = hmac.new(key_path.read_bytes(), body, hashlib.sha256).hexdigest()
        payload["signatureAlg"] = "hmac-sha256"
        payload["signatureKeyId"] = "hmac-dev"
        payload["signature"] = "hex:" + sig
        payload["signatureStatus"] = "hmac-sha256-dev"
        payload["signatureNote"] = (
            "Dev-only HMAC over canonical body using dev/receipt-keys/hmac-dev.key. "
            "Not production PKI; CI may verify when the key is present as a secret."
        )
        # Re-digest after signature fields? Signature is non-binding; digest stays.
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=OUT_DEFAULT,
        help="Output path (default: registry/support-matrix.json)",
    )
    parser.add_argument(
        "--sign-hmac",
        action="store_true",
        help="Attach a local-dev HMAC (writes/uses dev/receipt-keys/hmac-dev.key)",
    )
    args = parser.parse_args(argv)
    matrix = generate(sign_hmac=args.sign_hmac)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    verified = sum(
        1
        for c in matrix["capabilities"]
        if c["supportClaims"]["conformanceVerifiedEvidence"]
    )
    print(
        f"wrote {args.output.relative_to(ROOT)} "
        f"({len(matrix['capabilities'])} capabilities, "
        f"{verified} evidence-verified, signatureStatus={matrix['signatureStatus']}, "
        f"contentDigest={matrix['contentDigest']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
