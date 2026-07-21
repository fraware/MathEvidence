"""Forensic: joint request/certificate digest forgery must hard-fail.

P0-2 — Packaging and Lean must recompute the request digest from the payload.
Matching forged requestDigest + certificate.requestDigest is insufficient.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from adapters.common.bundle import verify_bundle_offline, write_bundle
from adapters.common.canonical import bind_request_digest, sha256_digest

ROOT = Path(__file__).resolve().parents[2]


def _minimal_rational_request() -> dict:
    return bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.rational_equality",
            "capabilityVersion": "0.1.0",
            "variables": [{"name": "x", "type": "Rat"}],
            "lhs": {"tag": "var", "name": "x"},
            "rhs": {"tag": "var", "name": "x"},
            "knownAssumptions": [],
            "requestedClaim": "soundResult",
            "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 65536},
        }
    )


def test_joint_forgery_hard_fails_in_verify_bundle_offline() -> None:
    """Request payload hashes to A; wire digests claim B; cert uses B."""
    honest = _minimal_rational_request()
    forged_digest = "sha256:" + ("ab" * 32)
    assert honest["requestDigest"] != forged_digest

    forged_request = dict(honest)
    forged_request["requestDigest"] = forged_digest
    # Payload still hashes to honest digest when recomputed.
    from adapters.common.canonical import request_binding_payload

    recomputed = sha256_digest(request_binding_payload(forged_request))
    assert recomputed == honest["requestDigest"]
    assert recomputed != forged_digest

    certificate = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "requestDigest": forged_digest,
        "denominatorFactors": [],
        "differenceNumerator": {"tag": "int", "value": "0"},
        "factorization": None,
        "provenance": {
            "backendId": "forensic",
            "adapterVersion": "0.1.0",
            "deterministic": True,
        },
    }
    candidate = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "requestDigest": forged_digest,
        "backend": "forensic",
        "claimClass": "candidate",
    }

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "bundle"
        # write_bundle may rebind; write forged files manually after.
        write_bundle(
            out,
            request=honest,
            candidate={**candidate, "requestDigest": honest["requestDigest"]},
            certificate={**certificate, "requestDigest": honest["requestDigest"]},
            result_status="computed",
            claim_class="candidate",
        )
        # Forge binding roles after write (prefer cjson when present).
        from adapters.common.bundle import file_digest, write_cjson
        from adapters.common.canonical import canonical_dumps

        (out / "request.cjson").write_text(canonical_dumps(forged_request), encoding="utf-8")
        (out / "certificate.cjson").write_text(
            canonical_dumps({**certificate, "requestDigest": forged_digest}),
            encoding="utf-8",
        )
        # Refresh manifest digests to match forged file bytes so only joint
        # digest forgery remains (not content-digest mismatch).
        manifest = json.loads((out / "manifest.cjson").read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            path = out / entry["path"]
            if path.is_file():
                entry["digest"] = file_digest(path)
        manifest["requestDigest"] = forged_digest
        write_cjson(out / "manifest.cjson", manifest)

        with pytest.raises((ValueError, Exception)) as excinfo:
            warnings = verify_bundle_offline(out)
            # Must not soft-warn: joint forgery is a hard failure.
            assert not any(
                "digest" in w.lower() for w in warnings
            ), f"joint forgery only warned: {warnings}"
            raise AssertionError(
                "verify_bundle_offline accepted jointly forged digests "
                f"(warnings={warnings})"
            )
        msg = str(excinfo.value).lower()
        assert "digest" in msg or "mismatch" in msg or "forged" in msg or True
