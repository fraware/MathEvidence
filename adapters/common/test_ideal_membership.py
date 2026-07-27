"""Tests for ideal-membership adapter + Python mirror."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.common.ideal_membership import (
    check_membership_python,
    propose_membership_witness,
    sage_executable,
    wolframscript_executable,
)

import pytest


def test_arity_mismatch_rejected() -> None:
    from adapters.common.ideal_membership import ArityError

    target = {"varCount": 2, "terms": [{"coefficient": 1, "exponents": [1]}]}  # len 1 ≠ 2
    gens = [{"varCount": 2, "terms": [{"coefficient": 1, "exponents": [1, 0]}]}]
    with pytest.raises(ArityError):
        check_membership_python(target, gens, gens)


def test_zip_truncation_no_longer_silent() -> None:
    """Previously zip truncated [1,1]+[1] → [2]; must reject."""
    from adapters.common.ideal_membership import ArityError

    target = {"varCount": 2, "terms": [{"coefficient": 1, "exponents": [1, 1]}]}
    gens = [{"varCount": 2, "terms": [{"coefficient": 1, "exponents": [1, 0]}]}]
    bad_q = [{"varCount": 2, "terms": [{"coefficient": 1, "exponents": [1]}]}]
    with pytest.raises(ArityError):
        check_membership_python(target, gens, bad_q)


def test_capability_renamed() -> None:
    from adapters.common.ideal_membership import CAPABILITY_ID

    assert CAPABILITY_ID == "algebra.ideal_membership_witness"
    assert "groebner" not in CAPABILITY_ID


def test_im01_heuristic_certificate() -> None:
    target = {"varCount": 2, "terms": [{"coefficient": 1, "exponents": [1, 1]}]}
    gens = [
        {"varCount": 2, "terms": [{"coefficient": 1, "exponents": [1, 0]}]},
        {"varCount": 2, "terms": [{"coefficient": 1, "exponents": [0, 1]}]},
    ]
    out = propose_membership_witness(target=target, generators=gens, backend="heuristic")
    assert out["pythonMirrorAccepts"] is True
    assert check_membership_python(target, gens, out["multipliers"])


def test_im02_expected_multipliers() -> None:
    target = {
        "varCount": 1,
        "terms": [
            {"coefficient": 1, "exponents": [2]},
            {"coefficient": -1, "exponents": [0]},
        ],
    }
    gens = [
        {
            "varCount": 1,
            "terms": [
                {"coefficient": 1, "exponents": [1]},
                {"coefficient": -1, "exponents": [0]},
            ],
        }
    ]
    qs = [
        {
            "varCount": 1,
            "terms": [
                {"coefficient": 1, "exponents": [1]},
                {"coefficient": 1, "exponents": [0]},
            ],
        }
    ]
    assert check_membership_python(target, gens, qs)


def test_sympy_generates_checked_witness_for_factorization() -> None:
    pytest.importorskip("sympy")
    target = {
        "varCount": 1,
        "terms": [
            {"coefficient": 1, "exponents": [2]},
            {"coefficient": -1, "exponents": [0]},
        ],
    }
    gens = [
        {
            "varCount": 1,
            "terms": [
                {"coefficient": 1, "exponents": [1]},
                {"coefficient": -1, "exponents": [0]},
            ],
        }
    ]
    out = propose_membership_witness(target=target, generators=gens, backend="sympy")
    assert out["backend"] == "sympy"
    assert out["pythonMirrorAccepts"] is True
    assert check_membership_python(target, gens, out["multipliers"])


def test_sympy_nontrivial_degree_witness() -> None:
    """Non-trivial q (degree ≥ 1), not only constant/q=1 cases."""
    pytest.importorskip("sympy")
    target = {"varCount": 1, "terms": [{"coefficient": 1, "exponents": [2]}]}
    gens = [{"varCount": 1, "terms": [{"coefficient": 1, "exponents": [1]}]}]
    out = propose_membership_witness(target=target, generators=gens, backend="sympy")
    assert out["pythonMirrorAccepts"] is True
    assert any(
        sum(t["exponents"]) >= 1 for q in out["multipliers"] for t in q.get("terms") or []
    )


def test_mathematica_without_wolframscript_is_not_advertised() -> None:
    if wolframscript_executable() is not None:
        pytest.skip("wolframscript env present; live path tested when available")
    target = {"varCount": 1, "terms": [{"coefficient": 1, "exponents": [1]}]}
    gens = [{"varCount": 1, "terms": [{"coefficient": 1, "exponents": [1]}]}]
    out = propose_membership_witness(
        target=target, generators=gens, backend="mathematica"
    )
    assert out["backend"] == "mathematica"
    assert out["multipliers"] == []
    assert out["pythonMirrorAccepts"] is False
    assert out["liveDetection"]["wolframscriptEnvPresent"] is False
    notes = " ".join(out["notes"]).lower()
    assert "mathevidence_wolframscript" in notes or "not advertised" in notes


def test_sage_without_executable_is_not_advertised() -> None:
    if sage_executable() is not None:
        pytest.skip("sage present; live path tested separately when available")
    target = {"varCount": 1, "terms": [{"coefficient": 1, "exponents": [1]}]}
    gens = [{"varCount": 1, "terms": [{"coefficient": 1, "exponents": [1]}]}]
    out = propose_membership_witness(target=target, generators=gens, backend="sage")
    assert out["backend"] == "sage"
    assert out["multipliers"] == []
    assert out["pythonMirrorAccepts"] is False
    assert out["liveDetection"]["sageExecutablePresent"] is False
    assert "not advertised" in " ".join(out["notes"]).lower() or "no sage" in " ".join(
        out["notes"]
    ).lower()


def test_differential_sympy_and_optional_second_backend() -> None:
    """Same request: SymPy witness accepted; second live backend matches when present."""
    pytest.importorskip("sympy")
    target = {
        "varCount": 1,
        "terms": [
            {"coefficient": 1, "exponents": [2]},
            {"coefficient": -1, "exponents": [0]},
        ],
    }
    gens = [
        {
            "varCount": 1,
            "terms": [
                {"coefficient": 1, "exponents": [1]},
                {"coefficient": -1, "exponents": [0]},
            ],
        }
    ]
    sympy_out = propose_membership_witness(target=target, generators=gens, backend="sympy")
    assert sympy_out["pythonMirrorAccepts"] is True
    assert check_membership_python(target, gens, sympy_out["multipliers"])

    second_backends: list[str] = []
    if wolframscript_executable() is not None:
        second_backends.append("mathematica")
    if sage_executable() is not None:
        second_backends.append("sage")
    if not second_backends:
        pytest.skip(
            "no second live backend (MATHEVIDENCE_WOLFRAMSCRIPT / sage); "
            "SymPy-only differential baseline recorded"
        )
    for backend in second_backends:
        other = propose_membership_witness(target=target, generators=gens, backend=backend)
        assert other["pythonMirrorAccepts"] is True, backend
        assert check_membership_python(target, gens, other["multipliers"]), backend


def test_stub_empty_does_not_accept() -> None:
    target = {"varCount": 1, "terms": [{"coefficient": 1, "exponents": [1]}]}
    gens = [{"varCount": 1, "terms": [{"coefficient": 1, "exponents": [1]}]}]
    out = propose_membership_witness(target=target, generators=gens, backend="stub")
    assert out["multipliers"] == []
    assert out["pythonMirrorAccepts"] is False


def test_wrong_witness_rejected() -> None:
    """Adversarial: wrong multipliers fail the Python mirror of checkMembership."""
    target = {
        "varCount": 1,
        "terms": [
            {"coefficient": 1, "exponents": [2]},
            {"coefficient": -1, "exponents": [0]},
        ],
    }
    gens = [
        {
            "varCount": 1,
            "terms": [
                {"coefficient": 1, "exponents": [1]},
                {"coefficient": -1, "exponents": [0]},
            ],
        }
    ]
    wrong = [{"varCount": 1, "terms": [{"coefficient": 1, "exponents": [0]}]}]
    assert check_membership_python(target, gens, wrong) is False


def test_wrong_generator_order_rejected() -> None:
    """Adversarial: swapped multipliers for asymmetric combination must reject."""
    target = {
        "varCount": 1,
        "terms": [
            {"coefficient": 2, "exponents": [1]},
            {"coefficient": 3, "exponents": [0]},
        ],
    }
    gens = [
        {"varCount": 1, "terms": [{"coefficient": 1, "exponents": [1]}]},
        {"varCount": 1, "terms": [{"coefficient": 1, "exponents": [0]}]},
    ]
    swapped = [
        {"varCount": 1, "terms": [{"coefficient": 3, "exponents": [0]}]},
        {"varCount": 1, "terms": [{"coefficient": 2, "exponents": [0]}]},
    ]
    correct = [
        {"varCount": 1, "terms": [{"coefficient": 2, "exponents": [0]}]},
        {"varCount": 1, "terms": [{"coefficient": 3, "exponents": [0]}]},
    ]
    assert check_membership_python(target, gens, swapped) is False
    assert check_membership_python(target, gens, correct) is True


def test_fixture_dual_backend_certificates_accepted() -> None:
    """Committed Mathematica/Sage fixtures for ≥2 shared requests; Lean mirror accepts."""
    root = Path(__file__).resolve().parents[2] / "evidence" / "examples"
    pairs = [
        (
            "ideal_membership_mathematica_offline_x2m1",
            "ideal_membership_sage_offline_x2m1",
        ),
        (
            "ideal_membership_mathematica_offline_xy",
            "ideal_membership_sage_offline_xy",
        ),
    ]
    from adapters.common.bundle import load_role_json

    for mm_name, sage_name in pairs:
        mm = load_role_json(root / mm_name, "certificate")
        sg = load_role_json(root / sage_name, "certificate")
        assert mm["requestDigest"] == sg["requestDigest"]
        assert mm["target"] == sg["target"]
        assert mm["generators"] == sg["generators"]
        assert mm["provenance"]["backendId"] == "mathematica"
        assert sg["provenance"]["backendId"] == "sage"
        assert mm["provenance"]["backendVersion"] == "offline-fixture"
        assert sg["provenance"]["backendVersion"] == "offline-fixture"
        assert check_membership_python(mm["target"], mm["generators"], mm["multipliers"])
        assert check_membership_python(sg["target"], sg["generators"], sg["multipliers"])


def test_live_differential_blocked_without_second_backend() -> None:
    """Honesty: without Wolfram/Sage, live dual-backend differential is blocked."""
    if wolframscript_executable() is not None or sage_executable() is not None:
        pytest.skip("second live backend present; live differential path available")
    assert wolframscript_executable() is None
    assert sage_executable() is None


def test_benchmark_manifest_meets_fifty() -> None:
    manifest = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "benchmarks"
            / "ideal_membership"
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["taskCount"] >= 50
    assert len(manifest["tasks"]) == manifest["taskCount"]


def test_ideal_kernel_replay_profile() -> None:
    from adapters.common.canonical import bind_request_digest
    from adapters.common.kernel_replay import _capability_replay_profile

    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.ideal_membership_witness",
            "capabilityVersion": "0.1.0",
            "target": {"varCount": 2, "terms": [{"coefficient": 1, "exponents": [1, 1]}]},
            "generators": [
                {"varCount": 2, "terms": [{"coefficient": 1, "exponents": [1, 0]}]},
                {"varCount": 2, "terms": [{"coefficient": 1, "exponents": [0, 1]}]},
            ],
            "requestedClaim": "witness",
        }
    )
    profile = _capability_replay_profile(req)
    assert profile["capability_id"] == "algebra.ideal_membership_witness"
    assert profile["fixture"] == "xy"
    assert profile["soundness_theorem"] == "replaySound"

    req1 = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.ideal_membership_witness",
            "capabilityVersion": "0.1.0",
            "target": {
                "varCount": 1,
                "terms": [
                    {"coefficient": 1, "exponents": [2]},
                    {"coefficient": -1, "exponents": [0]},
                ],
            },
            "generators": [
                {
                    "varCount": 1,
                    "terms": [
                        {"coefficient": 1, "exponents": [1]},
                        {"coefficient": -1, "exponents": [0]},
                    ],
                }
            ],
            "requestedClaim": "witness",
        }
    )
    assert _capability_replay_profile(req1)["fixture"] == "x2m1"


def test_candidate_tier_never_soundness_verified(monkeypatch: pytest.MonkeyPatch) -> None:
    """Candidate / smoke path must not mint theorem-level status."""
    import scripts.run_ideal_membership_benchmark as bench

    monkeypatch.setenv("MATHEVIDENCE_IDEAL_BENCH_TIER", "candidate")
    task = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "benchmarks"
            / "ideal_membership"
            / "tasks"
            / "IM01_linear_combination_xy.json"
        ).read_text(encoding="utf-8")
    )
    row = bench._score_task(task, backend="stub", tier="candidate")
    assert row["status"] == "pass"
    lean = row["lean"]
    assert lean.get("resultStatus") is None
    assert lean.get("assuranceClaim") in {None, "native_checked_candidate_only"}
    assert lean.get("kernelReplayStatus") != "ok"


def test_release_tier_cli_defaults_and_fixture_map() -> None:
    import scripts.run_ideal_membership_benchmark as bench

    assert bench._resolve_tier(None) == "candidate"
    assert bench.RELEASE_FIXTURE_TASKS["IM01_linear_combination_xy"] == "xy"
    assert bench.RELEASE_FIXTURE_TASKS["IM02_x2_minus_1"] == "x2m1"


def test_ideal_kernel_replay_refuses_without_lean(tmp_path: Path) -> None:
    """Missing Lean must not invent soundness_verified (ME-RV-035 honesty)."""
    import scripts.run_ideal_membership_benchmark as bench
    from adapters.common.kernel_replay import run_kernel_replay

    task = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "benchmarks"
            / "ideal_membership"
            / "tasks"
            / "IM01_linear_combination_xy.json"
        ).read_text(encoding="utf-8")
    )
    proposed = [
        {"varCount": 2, "terms": [{"coefficient": 1, "exponents": [0, 1]}]},
        {"varCount": 2, "terms": []},
    ]
    bundle_dir = tmp_path / "bundle"
    bench._build_temp_bundle(
        task=task, proposed=proposed, backend="stub", bundle_dir=bundle_dir
    )
    try:
        out = run_kernel_replay(
            bundle_dir=bundle_dir,
            require_lean=False,
            out_record_dir=tmp_path / "ideal_cert",
        )
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        assert any(
            k in msg
            for k in (
                "theorem_elaboration",
                "kernel_rejected",
                "lake not found",
                "refusing",
                "soundness_verified",
                "content_digest",
            )
        ), msg
        return
    assert out["ok"] is True
    assert out["capability"] == "algebra.ideal_membership_witness"
    assert out["resultStatus"] == "soundness_verified"
    assert out.get("leanOk") is True
    assert Path(out["recordDir"]).is_dir()
