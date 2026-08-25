"""Wave 4 forensic tests: LA/CEX mirrors and exact-replay fail-closed policy."""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.common.canonical import bind_request_digest
from adapters.common.kernel_replay import (
    KernelReplayError,
    _capability_replay_profile,
    run_kernel_replay,
)
from adapters.common.lean_mirrors import check_finite_counterexample, check_linear_algebra

ROOT = Path(__file__).resolve().parents[2]


def _rat(n: int, d: int = 1) -> dict:
    return {"tag": "rat", "num": str(n), "den": str(d)}


def test_la_profile_and_generic_kernel_replay_fails_closed(tmp_path: Path) -> None:
    """LA keeps its checker profile but cannot mint a generic record from a fixture."""
    bundle = ROOT / "evidence" / "conformance" / "linear_algebra" / "inverse_witness_2x2" / "bundle"
    if not bundle.is_dir():
        pytest.skip("LA conformance bundle missing")
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "inverse_witness",
            "matrix": {
                "tag": "matrix",
                "rows": 2,
                "cols": 2,
                "entries": [[_rat(1, 2), _rat(0)], [_rat(0), _rat(2)]],
            },
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )
    profile = _capability_replay_profile(req)
    assert profile["capability_id"] == "algebra.linear_algebra"
    assert profile["soundness_theorem"] == "replaySound"
    assert profile["fixture"] == "inv"  # historical self-test hint only

    with pytest.raises(KernelReplayError) as exc:
        run_kernel_replay(
            bundle_dir=bundle,
            require_lean=False,
            out_record_dir=tmp_path / "la_cert",
        )
    assert exc.value.code == "assurance_mode_unavailable"
    assert "exact-candidate generator" in str(exc.value)
    assert not (tmp_path / "la_cert").exists()


def test_cex_profile_and_generic_kernel_replay_fails_closed(tmp_path: Path) -> None:
    """CEX fixture replay is a protocol test, not arbitrary Certification authority."""
    bundle = (
        ROOT
        / "evidence"
        / "conformance"
        / "finite_counterexample"
        / "simple_false_universal"
        / "bundle"
    )
    if not bundle.is_dir():
        pytest.skip("CEX conformance bundle missing")
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "logic.finite_counterexample",
            "capabilityVersion": "0.1.0",
            "predicate": {
                "varNames": ["x"],
                "domains": [{"ty": "nat", "bound": 3}],
                "pred": {
                    "tag": "eq",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "lit", "v": {"tag": "nat", "v": 0}},
                },
            },
            "requestedClaim": "refutation",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 65536},
        }
    )
    profile = _capability_replay_profile(req)
    assert profile["capability_id"] == "logic.finite_counterexample"
    assert profile["fixture"] == "nat_eq0"  # historical self-test hint only

    with pytest.raises(KernelReplayError) as exc:
        run_kernel_replay(
            bundle_dir=bundle,
            require_lean=False,
            out_record_dir=tmp_path / "cex_cert",
        )
    assert exc.value.code == "assurance_mode_unavailable"
    assert "exact-candidate generator" in str(exc.value)
    assert not (tmp_path / "cex_cert").exists()


def test_la_adversarial_mirrors() -> None:
    # Dimension mismatch
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "system_solution",
            "matrix": {
                "tag": "matrix",
                "rows": 2,
                "cols": 2,
                "entries": [[_rat(1), _rat(1)], [_rat(0), _rat(1)]],
            },
            "rhs": [_rat(3), _rat(2)],
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )
    short = {
        "requestDigest": req["requestDigest"],
        "operation": "system_solution",
        "vector": [_rat(1)],
    }
    assert check_linear_algebra(req, short) is False

    # Transposed-style wrong solution
    bad = {
        "requestDigest": req["requestDigest"],
        "operation": "system_solution",
        "vector": [_rat(3), _rat(2)],
    }
    assert check_linear_algebra(req, bad) is False

    # Zero kernel vector
    ker_req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "kernel_vector",
            "matrix": {
                "tag": "matrix",
                "rows": 2,
                "cols": 2,
                "entries": [[_rat(1), _rat(2)], [_rat(2), _rat(4)]],
            },
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )
    zero = {
        "requestDigest": ker_req["requestDigest"],
        "operation": "kernel_vector",
        "vector": [_rat(0), _rat(0)],
    }
    assert check_linear_algebra(ker_req, zero) is False

    # Det sign error
    det_req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "det_identity",
            "matrix": {
                "tag": "matrix",
                "rows": 2,
                "cols": 2,
                "entries": [[_rat(1), _rat(2)], [_rat(3), _rat(4)]],
            },
            "claimedDet": _rat(2),
            "requestedClaim": "soundResult",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )
    det_cert = {
        "requestDigest": det_req["requestDigest"],
        "operation": "det_identity",
    }
    assert check_linear_algebra(det_req, det_cert) is False


def test_cex_adversarial_mirrors() -> None:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "logic.finite_counterexample",
            "capabilityVersion": "0.1.0",
            "predicate": {
                "varNames": ["x"],
                "domains": [{"ty": "nat", "bound": 3}],
                "pred": {
                    "tag": "eq",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "lit", "v": {"tag": "nat", "v": 0}},
                },
            },
            "requestedClaim": "refutation",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 65536},
        }
    )
    digest = req["requestDigest"]
    # False witness (makes predicate true)
    assert (
        check_finite_counterexample(
            req, {"requestDigest": digest, "witness": {"assignment": [{"tag": "nat", "v": 0}]}}
        )
        is False
    )
    # Request digest mismatch
    assert (
        check_finite_counterexample(
            req,
            {
                "requestDigest": "sha256:" + ("0" * 64),
                "witness": {"assignment": [{"tag": "nat", "v": 1}]},
            },
        )
        is False
    )


def test_kernel_replay_missing_bundle_errors() -> None:
    with pytest.raises(KernelReplayError) as exc:
        run_kernel_replay(bundle_dir=ROOT / "no_such_bundle", require_lean=False)
    assert "bundle_not_found" in str(exc.value).lower() or exc.value.code in {
        "bundle_not_found",
        "malformed_evidence",
    }
