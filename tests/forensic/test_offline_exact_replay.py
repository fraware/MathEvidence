"""SPEC-09 offline exact-replay bundle + tamper matrix (no Lake required)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from adapters.common.exact_replay.offline_bundle import (
    both_modes_agree,
    build_offline_exact_bundle,
    mutate_bundle_for_tamper,
    replay_offline_exact_bundle,
)

ROOT = Path(__file__).resolve().parents[2]


def _poly(m: int, coefficient: int, exponents: list[int]) -> dict:
    return {
        "varCount": m,
        "terms": [{"coefficient": coefficient, "exponents": exponents}],
    }


def _ideal_payload() -> tuple[dict, dict, str]:
    from adapters.common.canonical import bind_request_digest

    request = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.ideal_membership_witness",
            "capabilityVersion": "0.1.0",
            "target": _poly(2, 1, [1, 1]),
            "generators": [_poly(2, 1, [1, 0]), _poly(2, 1, [0, 1])],
            "requestedClaim": "witness",
        }
    )
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"],
        "requestDigest": request["requestDigest"],
        "target": request["target"],
        "generators": request["generators"],
        "multipliers": [_poly(2, 1, [0, 1]), {"varCount": 2, "terms": []}],
        "claimClass": "witness",
    }
    return request, certificate, "sha256:" + ("3" * 64)


@pytest.fixture(autouse=True)
def _offline_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MATHEVIDENCE_OFFLINE", "1")
    monkeypatch.delenv("MATHEVIDENCE_ALLOW_NETWORK", raising=False)
    monkeypatch.delenv("MATHEVIDENCE_OFFLINE_LEAN", raising=False)


def _build(tmp_path: Path) -> Path:
    request, certificate, cand = _ideal_payload()
    out = tmp_path / "bundle"
    build_offline_exact_bundle(
        out,
        capability_id="algebra.ideal_membership_witness",
        request=request,
        certificate=certificate,
        candidate_bundle_digest=cand,
        module_name="MathEvidence.Generated.Replay.exact_offline_xy",
        declaration_name="exact_offline_xy",
        repo_root=ROOT,
    )
    return out


def test_build_and_both_modes_agree(tmp_path: Path) -> None:
    bundle = _build(tmp_path)
    a, b = both_modes_agree(bundle, repo_root=ROOT)
    assert a.ok and b.ok
    assert a.logical_outcome == b.logical_outcome == "theorem_pending"
    assert a.generated_source_hash == b.generated_source_hash
    assert a.generated_source_hash.startswith("sha256:")
    # No absolute paths in sealed roles.
    text = (bundle / "exact-replay-manifest.cjson").read_text(encoding="utf-8")
    assert "/Users/" not in text
    assert "C:\\" not in text


def test_network_allow_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = _build(tmp_path)
    monkeypatch.setenv("MATHEVIDENCE_ALLOW_NETWORK", "1")
    result = replay_offline_exact_bundle(bundle, repo_root=ROOT)
    assert not result.ok
    assert result.logical_outcome == "setup_integrity_error"


@pytest.mark.parametrize(
    "case",
    [
        "candidate",
        "generated_source",
        "artifact_delete",
        "artifact_mutate",
        "manifest",
        "generator_version",
        "declaration_identity",
        "toolchain_lock",
        "capability_id",
        "capability_version",
    ],
)
def test_tamper_matrix(tmp_path: Path, case: str) -> None:
    bundle = _build(tmp_path)
    good = replay_offline_exact_bundle(bundle, repo_root=ROOT)
    assert good.ok
    mutate_bundle_for_tamper(bundle, case=case)
    bad = replay_offline_exact_bundle(bundle, repo_root=ROOT)
    assert not bad.ok, f"tamper case {case} should fail"
    assert bad.logical_outcome in {"tamper_detected", "setup_integrity_error"}
    # Missing deps / lock mismatches must not look like theorem failures.
    assert "theorem_failure" not in (bad.detail or "")
    assert bad.error_kind in {"tamper", "setup_integrity"}


def test_missing_dependency_is_setup_error(tmp_path: Path) -> None:
    bundle = _build(tmp_path)
    (bundle / "toolchain-contract.cjson").unlink()
    bad = replay_offline_exact_bundle(bundle, repo_root=ROOT)
    assert not bad.ok
    assert bad.logical_outcome == "setup_integrity_error"
    assert bad.error_kind == "setup_integrity"


def test_offline_lean_inspect_can_prove_when_required(tmp_path: Path) -> None:
    """Opt-in Lean inspect exits theorem_proved (or honest setup error).

    Uses a wire-parity requestDigest so Lean ``Request.ofWireFields!`` binding
    can close. ``theorem_failure`` remains reserved for real math/identity
    rejection after deps are present.
    """
    from adapters.common.kernel_replay import find_lake

    if find_lake(ROOT) is None:
        pytest.skip("lake not available")
    bundle = _build(tmp_path)
    result = replay_offline_exact_bundle(
        bundle, repo_root=ROOT, require_lean=True
    )
    assert result.logical_outcome in {"theorem_proved", "setup_integrity_error"}, (
        f"unexpected outcome={result.logical_outcome!r} detail={result.detail!r}"
    )
    if result.logical_outcome == "theorem_proved":
        assert result.ok is True
        assert result.error_kind is None
        extras = result.extras or {}
        assert isinstance(extras.get("theoremTypeDigest"), str)
        assert str(extras["theoremTypeDigest"]).startswith("sha256:")
    else:
        assert result.ok is False
        assert result.error_kind == "setup_integrity"
        assert "theorem_failure" not in (result.detail or "")


def test_tamper_matrix_rejects_theorem_failure_label(tmp_path: Path) -> None:
    """Tamper / setup paths must not be reported as theorem_failure."""
    bundle = _build(tmp_path)
    mutate_bundle_for_tamper(bundle, case="generated_source")
    bad = replay_offline_exact_bundle(bundle, repo_root=ROOT)
    assert not bad.ok
    assert bad.logical_outcome != "theorem_failure"
    assert bad.error_kind in {"tamper", "setup_integrity"}

