"""Bundle v0.2 canonical .cjson layout + dual-read of legacy .json."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.common.bundle import (
    BUNDLE_VERSION,
    file_digest,
    find_role_path,
    load_role_json,
    verify_bundle_offline,
    write_bundle,
)
from adapters.common.canonical import bind_request_digest, canonical_dumps

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "evidence" / "examples" / "rational_equality_basic"


def _minimal_rational_request() -> dict:
    req = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [{"name": "x", "type": "Rat"}],
        "lhs": {
            "tag": "add",
            "left": {"tag": "var", "name": "x"},
            "right": {"tag": "int", "value": "0"},
        },
        "rhs": {"tag": "var", "name": "x"},
        "knownAssumptions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
    }
    return bind_request_digest(req)


def _minimal_certificate(request_digest: str) -> dict:
    return {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "requestDigest": request_digest,
        "differenceNumerator": {"tag": "int", "value": "0"},
        "denominatorFactors": [],
        "factorization": {"method": "test", "notes": "unit"},
        "provenance": {
            "backendId": "test",
            "backendVersion": "0",
            "adapterVersion": "0.1.0",
            "generatedAt": "2026-07-21T00:00:00Z",
            "deterministic": True,
        },
    }


def test_write_bundle_emits_v02_cjson_roles(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    candidate = {"schemaVersion": "0.1.0", "notes": "candidate"}
    out = tmp_path / "bundle"
    manifest = write_bundle(
        out,
        request=request,
        candidate=candidate,
        certificate=cert,
        result_status="computed",
    )
    assert manifest["bundleVersion"] == BUNDLE_VERSION
    for stem in (
        "request",
        "candidate",
        "certificate",
        "manifest",
        "axiom-report",
    ):
        path = out / f"{stem}.cjson"
        assert path.is_file(), stem
        # Canonical bytes: no pretty indentation.
        text = path.read_text(encoding="utf-8")
        assert "\n" not in text or text == canonical_dumps(json.loads(text))
        assert path.read_text(encoding="utf-8") == canonical_dumps(json.loads(text))
    assert (out / "theorem.lean").is_file()
    assert (out / "README.md").is_file()
    assert not (out / "checker-receipt.cjson").is_file()
    # Digests in manifest match on-disk bytes.
    for entry in manifest["files"]:
        assert file_digest(out / entry["path"]) == entry["digest"]
    warnings = verify_bundle_offline(out)
    assert isinstance(warnings, list)


def test_write_bundle_refuses_verified_without_receipt(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    out = tmp_path / "bundle"
    manifest = write_bundle(
        out,
        request=request,
        candidate={},
        certificate=cert,
        result_status="soundness_verified",
    )
    assert manifest["resultStatus"] == "computed"


def test_migrated_v02_example_verifies() -> None:
    warnings = verify_bundle_offline(EXAMPLE)
    assert isinstance(warnings, list)
    assert find_role_path(EXAMPLE, "request") == EXAMPLE / "request.cjson"
    req = load_role_json(EXAMPLE, "request")
    assert req["capability"] == "algebra.rational_equality"
    manifest = load_role_json(EXAMPLE, "manifest")
    assert manifest["bundleVersion"] == BUNDLE_VERSION


def test_legacy_v01_dual_read_still_supported(tmp_path: Path) -> None:
    """Dual-read: a hand-built v0.1 .json-only tree still verifies."""
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    bundle = tmp_path / "legacy"
    bundle.mkdir()
    (bundle / "request.json").write_text(
        json.dumps(request, indent=2) + "\n", encoding="utf-8"
    )
    (bundle / "candidate.json").write_text("{}\n", encoding="utf-8")
    (bundle / "certificate.json").write_text(
        json.dumps(cert, indent=2) + "\n", encoding="utf-8"
    )
    from adapters.common.bundle import build_manifest, file_digest, write_json

    files = []
    for name in ("request.json", "candidate.json", "certificate.json"):
        files.append(
            {
                "path": name,
                "digest": file_digest(bundle / name),
                "mediaType": "application/json",
            }
        )
    manifest = build_manifest(
        capability_id="algebra.rational_equality",
        capability_version="0.1.0",
        request_digest=request["requestDigest"],
        claim_class="candidate",
        result_status="computed",
        assurance_mode="kernel_replay",
        files=files,
        provenance={"leanVersion": "test", "libraryRevision": "test", "checkerVersion": "0"},
        bundle_version="0.1.0",
    )
    write_json(bundle / "manifest.json", manifest)
    warnings = verify_bundle_offline(bundle)
    assert isinstance(warnings, list)
    assert find_role_path(bundle, "request") == bundle / "request.json"


def test_required_roles_content_digests(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    out = tmp_path / "bundle"
    write_bundle(
        out,
        request=request,
        candidate={"ok": True},
        certificate=cert,
    )
    # Tamper a binding file → digest mismatch.
    path = out / "certificate.cjson"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_tamper"] = True
    path.write_text(canonical_dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_bundle_offline(out)
