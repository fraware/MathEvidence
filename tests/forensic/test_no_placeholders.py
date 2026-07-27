"""Forensic: Wave 0 / ME-RV-002 placeholder rejection."""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.common.bundle import (
    PLACEHOLDER_AXIOM_STATUS,
    PLACEHOLDER_THEOREM_NAME,
    write_bundle,
)
from adapters.common.canonical import bind_request_digest


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


def test_write_bundle_is_candidate_only_without_theorem_axiom(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    out = tmp_path / "bundle"
    manifest = write_bundle(
        out,
        request=request,
        candidate={"notes": "candidate"},
        certificate=cert,
        result_status="computed",
    )
    assert not (out / "theorem.lean").exists()
    assert not (out / "axiom-report.cjson").exists()
    assert manifest["resultStatus"] == "computed"
    assert manifest["assuranceMode"] == "native_checked"
    paths = {e["path"] for e in manifest["files"]}
    assert "theorem.lean" not in paths
    assert "axiom-report.cjson" not in paths


def test_write_bundle_rejects_placeholder_theorem(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    with pytest.raises(ValueError, match=PLACEHOLDER_THEOREM_NAME):
        write_bundle(
            tmp_path / "bundle",
            request=request,
            candidate={},
            certificate=cert,
            theorem_lean=(
                f"theorem {PLACEHOLDER_THEOREM_NAME} : True := trivial\n"
            ),
        )


def test_write_bundle_rejects_pending_compiled_audit(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    with pytest.raises(ValueError, match=PLACEHOLDER_AXIOM_STATUS):
        write_bundle(
            tmp_path / "bundle",
            request=request,
            candidate={},
            certificate=cert,
            axiom_report={
                "schemaVersion": "0.2.0",
                "status": PLACEHOLDER_AXIOM_STATUS,
                "leanVersion": "4.x",
                "libraryRevision": "workspace",
                "findings": [],
            },
        )
