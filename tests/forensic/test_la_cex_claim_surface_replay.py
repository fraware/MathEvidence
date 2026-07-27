"""ME-RV-041 / ME-RV-043: LA + CEX claim-surface kernel-replay fixtures."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from adapters.common.kernel_replay import _capability_replay_profile

ROOT = Path(__file__).resolve().parents[2]


def _load_generate_module():
    path = ROOT / "scripts" / "generate_replay_module.py"
    spec = importlib.util.spec_from_file_location("generate_replay_module", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gen = _load_generate_module()
_FIXTURE_MODULES = _gen._FIXTURE_MODULES
generate_from_target = _gen.generate_from_target


def test_la_operation_fixture_map() -> None:
    for op, fx in (
        ("inverse_witness", "inv"),
        ("system_solution", "sys"),
        ("kernel_vector", "ker"),
        ("det_identity", "det"),
    ):
        profile = _capability_replay_profile(
            {"capability": "algebra.linear_algebra", "operation": op}
        )
        assert profile["fixture"] == fx
        assert fx in _FIXTURE_MODULES
        assert "replaySound" in _FIXTURE_MODULES[fx]["proof"]


def test_cex_bool_and_nat_fixture_selection() -> None:
    nat_profile = _capability_replay_profile(
        {
            "capability": "logic.finite_counterexample",
            "predicate": {
                "varNames": ["x"],
                "domains": [{"ty": "nat", "bound": 3}],
            },
        }
    )
    assert nat_profile["fixture"] == "nat_eq0"
    bool_profile = _capability_replay_profile(
        {
            "capability": "logic.finite_counterexample",
            "predicate": {
                "varNames": ["b"],
                "domains": [{"ty": "bool"}],
            },
        }
    )
    assert bool_profile["fixture"] == "bool_false"
    assert "bool_false" in _FIXTURE_MODULES


@pytest.mark.parametrize("fixture", ["sys", "ker", "det", "bool_false", "inv", "nat_eq0"])
def test_generated_modules_bind_offline_fixtures(fixture: str) -> None:
    text = generate_from_target(
        {
            "moduleName": f"MathEvidence.Generated.Replay.Forensic{fixture}",
            "declarationName": f"certified_{fixture}_forensic",
            "theoremTypeCanonical": f"forensic {fixture}",
            "requestDigest": "sha256:" + ("ab" * 32),
            "candidateBundleDigest": "sha256:" + ("cd" * 32),
            "capability": (
                "logic.finite_counterexample"
                if fixture in ("nat_eq0", "bool_false")
                else "algebra.linear_algebra"
            ),
            "fixture": fixture,
        },
        fixture=fixture,
    )
    fx = _FIXTURE_MODULES[fixture]
    assert fx["req"] in text
    assert fx["cert"] in text
    assert "replaySound" in text
    assert "#print axioms" in text


def test_example_bundles_declare_supported_operations() -> None:
    inv_req = json.loads(
        (ROOT / "evidence/examples/linear_algebra_inverse_2x2/request.cjson").read_text(
            encoding="utf-8"
        )
    )
    assert inv_req["operation"] == "inverse_witness"
    cex_req = json.loads(
        (ROOT / "evidence/examples/finite_counterexample_nat_eq0/request.cjson").read_text(
            encoding="utf-8"
        )
    )
    assert cex_req["capability"] == "logic.finite_counterexample"
    profile = _capability_replay_profile(cex_req)
    assert profile["fixture"] == "nat_eq0"
