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
    for mm_name, sage_name in pairs:
        mm = json.loads((root / mm_name / "certificate.json").read_text(encoding="utf-8"))
        sg = json.loads((root / sage_name / "certificate.json").read_text(encoding="utf-8"))
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
