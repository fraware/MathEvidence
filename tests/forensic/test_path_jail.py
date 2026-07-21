"""Forensic: Agent path resolution must reject absolute and traversal paths.

P0-5 — public Agent API accepts opaque bundleId only; raw `path` is rejected.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from agent.api import service

ROOT = Path(__file__).resolve().parents[2]


def test_absolute_path_rejected_on_open_bundle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        abs_path = str(Path(tmp).resolve())
        assert Path(abs_path).is_absolute()
        out = service.op_open_bundle({"path": abs_path})
        assert out["resultStatus"] == "rejected", (
            "P0-5: absolute paths must be rejected; got "
            f"{out.get('resultStatus')}: {out.get('error')}"
        )
        err = out.get("error") or {}
        code = str(err.get("code", "")).lower()
        msg = str(err.get("message", "")).lower()
        assert (
            "path" in code
            or "traversal" in code
            or "absolute" in msg
            or "root" in msg
            or "jail" in msg
            or "bundle" in code
            or "schema" in msg
            or "additional" in msg
        ), f"expected path-jail / schema error, got {err}"


def test_traversal_path_rejected_on_open_bundle() -> None:
    out = service.op_open_bundle({"path": "../"})
    assert out["resultStatus"] == "rejected", (
        f"P0-5: traversal path accepted: {out}"
    )


def test_public_api_rejects_path_even_under_evidence() -> None:
    out = service.op_open_bundle({"path": "evidence/examples/rational_equality_basic"})
    assert out["resultStatus"] == "rejected"
    code = str((out.get("error") or {}).get("code", "")).lower()
    assert "path" in code or "forbidden" in code or "malformed" in code


def test_absolute_write_bundle_rejected_on_compute() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        abs_out = str(Path(tmp).resolve() / "evil")
        out = service.op_compute_evidence(
            {
                "capability": "algebra.rational_equality",
                "backend": "sympy",
                "request": {
                    "schemaVersion": "0.1.0",
                    "capability": "algebra.rational_equality",
                    "capabilityVersion": "0.1.0",
                    "varNames": ["x"],
                    "lhs": {"tag": "var", "name": "x"},
                    "rhs": {"tag": "var", "name": "x"},
                    "requestedClaim": "soundResult",
                    "resourcePolicy": {
                        "maxWallTimeMs": 5000,
                        "maxOutputBytes": 65536,
                    },
                },
                "writeBundleTo": abs_out,
            }
        )
        # Absolute write target must not succeed as a path escape.
        if out.get("resultStatus") in ("computed", "tested"):
            assert out.get("bundleRef") is None or not Path(abs_out).exists(), (
                "P0-5: compute wrote bundle to absolute path outside opaque store"
            )
        else:
            assert out["resultStatus"] in ("rejected", "unsupported")
