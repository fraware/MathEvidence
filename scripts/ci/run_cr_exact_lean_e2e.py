"""Release gate: execute production-generated exact candidates with pinned Lean.

This is intentionally a CI/release proof-of-execution gate, not a second verifier.
Each case goes through the registered production exact-replay plugin, then the
generated Lean source is elaborated by ``lake env lean`` under the repository
toolchain.  CR eligibility must never be inferred from source generation alone.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import adapters.common.exact_replay.plugins  # noqa: F401
from adapters.common.bounded_process import run_bounded
from adapters.common.exact_replay.pipeline import generate_module, verify
from adapters.common.limits import ResourceLimits
from agent.api.assurance_policy import decide_exact_kernel_replay, load_assurance_policy

ROOT = Path(__file__).resolve().parents[2]
BUNDLE_DIGEST = "sha256:" + ("c" * 64)
LIMITS = ResourceLimits(max_wall_time_ms=180_000, max_output_bytes=4_194_304)


@dataclass(frozen=True)
class ExactCase:
    name: str
    capability: str
    request: dict[str, Any]
    certificate: dict[str, Any]


def _digest(char: str) -> str:
    return "sha256:" + (char * 64)


def _rat(num: str | int, den: str | int = "1") -> dict[str, Any]:
    return {"tag": "rat", "num": str(num), "den": str(den)}


def _matrix(rows: list[list[tuple[str | int, str | int]]]) -> dict[str, Any]:
    return {
        "tag": "matrix",
        "rows": len(rows),
        "cols": len(rows[0]),
        "entries": [[_rat(num, den) for num, den in row] for row in rows],
    }


def _poly(var_count: int, coefficient: int, exponents: list[int]) -> dict[str, Any]:
    return {
        "varCount": var_count,
        "terms": [{"coefficient": coefficient, "exponents": exponents}],
    }


def _ideal_case() -> ExactCase:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.ideal_membership_witness",
        "capabilityVersion": "0.1.0",
        "target": _poly(2, 1, [1, 1]),
        "generators": [_poly(2, 1, [1, 0]), _poly(2, 1, [0, 1])],
        "requestedClaim": "witness",
        "requestDigest": _digest("1"),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"],
        "requestDigest": request["requestDigest"],
        "target": request["target"],
        "generators": request["generators"],
        "multipliers": [
            _poly(2, 1, [0, 1]),
            {"varCount": 2, "terms": []},
        ],
        "claimClass": "witness",
    }
    return ExactCase("ideal_membership", request["capability"], request, certificate)


def _rational_case() -> ExactCase:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [],
        "lhs": {"tag": "rat", "num": "2", "den": "4"},
        "rhs": {"tag": "rat", "num": "1", "den": "2"},
        "knownAssumptions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": _digest("2"),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"],
        "requestDigest": request["requestDigest"],
        "differenceNumerator": {"tag": "int", "value": "0"},
        "denominatorFactors": [],
        "provenance": {"backendId": "release-e2e", "adapterVersion": "0.1.0"},
    }
    return ExactCase("rational_equality", request["capability"], request, certificate)


def _linear_cases() -> list[ExactCase]:
    base = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
    }

    inv_req = {
        **base,
        "operation": "inverse_witness",
        "matrix": _matrix([[("2", "1")]]),
        "requestedClaim": "witness",
        "requestDigest": _digest("3"),
    }
    inv_cert = {
        "schemaVersion": "0.1.0",
        "capability": base["capability"],
        "capabilityVersion": base["capabilityVersion"],
        "requestDigest": inv_req["requestDigest"],
        "operation": "inverse_witness",
        "inverse": _matrix([[("1", "2")]]),
        "provenance": {"backendId": "release-e2e", "adapterVersion": "0.1.0"},
    }

    sys_req = {
        **base,
        "operation": "system_solution",
        "matrix": _matrix([[("2", "1")]]),
        "rhs": [_rat("4")],
        "requestedClaim": "witness",
        "requestDigest": _digest("4"),
    }
    sys_cert = {
        "schemaVersion": "0.1.0",
        "capability": base["capability"],
        "capabilityVersion": base["capabilityVersion"],
        "requestDigest": sys_req["requestDigest"],
        "operation": "system_solution",
        "vector": [_rat("2")],
        "provenance": {"backendId": "release-e2e", "adapterVersion": "0.1.0"},
    }

    ker_req = {
        **base,
        "operation": "kernel_vector",
        "matrix": _matrix([
            [("1", "1"), ("1", "1")],
            [("2", "1"), ("2", "1")],
        ]),
        "requestedClaim": "witness",
        "requestDigest": _digest("5"),
    }
    ker_cert = {
        "schemaVersion": "0.1.0",
        "capability": base["capability"],
        "capabilityVersion": base["capabilityVersion"],
        "requestDigest": ker_req["requestDigest"],
        "operation": "kernel_vector",
        "vector": [_rat("1"), _rat("-1")],
        "provenance": {"backendId": "release-e2e", "adapterVersion": "0.1.0"},
    }

    det_req = {
        **base,
        "operation": "det_identity",
        "matrix": _matrix([
            [("1", "1"), ("2", "1")],
            [("3", "1"), ("4", "1")],
        ]),
        "claimedDet": _rat("-2"),
        "requestedClaim": "soundResult",
        "requestDigest": _digest("6"),
    }
    det_cert = {
        "schemaVersion": "0.1.0",
        "capability": base["capability"],
        "capabilityVersion": base["capabilityVersion"],
        "requestDigest": det_req["requestDigest"],
        "operation": "det_identity",
        "provenance": {"backendId": "release-e2e", "adapterVersion": "0.1.0"},
    }

    return [
        ExactCase("linear_inverse", base["capability"], inv_req, inv_cert),
        ExactCase("linear_system", base["capability"], sys_req, sys_cert),
        ExactCase("linear_kernel", base["capability"], ker_req, ker_cert),
        ExactCase("linear_determinant", base["capability"], det_req, det_cert),
    ]


def _counterexample_case() -> ExactCase:
    request = {
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
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": _digest("7"),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"],
        "requestDigest": request["requestDigest"],
        "witness": {"assignment": [{"tag": "nat", "v": 2}]},
        "provenance": {"backendId": "release-e2e", "adapterVersion": "0.1.0"},
    }
    return ExactCase("finite_counterexample", request["capability"], request, certificate)


def _formal_calculus_case() -> ExactCase:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.formal_rational_calculus",
        "capabilityVersion": "0.1.0",
        "operation": "derivative_candidate",
        "variables": [{"name": "x", "type": "Rat"}],
        "independentVar": "x",
        "expr": {"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
        "candidate": {
            "tag": "mul",
            "left": {"tag": "int", "value": "2"},
            "right": {"tag": "var", "name": "x"},
        },
        "domainConditions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": _digest("8"),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"],
        "requestDigest": request["requestDigest"],
        "operation": "derivative_candidate",
        "domainConditions": [],
        "provenance": {"backendId": "release-e2e", "adapterVersion": "0.1.0"},
    }
    return ExactCase("formal_calculus", request["capability"], request, certificate)


def _analytic_case() -> ExactCase:
    source = {
        "tag": "mul",
        "lhs": {"tag": "variable", "idx": 0},
        "rhs": {"tag": "variable", "idx": 0},
    }
    target = {
        "tag": "add",
        "lhs": {
            "tag": "mul",
            "lhs": {"tag": "const", "value": "1"},
            "rhs": {"tag": "variable", "idx": 0},
        },
        "rhs": {
            "tag": "mul",
            "lhs": {"tag": "variable", "idx": 0},
            "rhs": {"tag": "const", "value": "1"},
        },
    }
    request = {
        "schemaVersion": "0.1.0",
        "capability": "analysis.analytic_calculus",
        "capabilityVersion": "0.1.0",
        "kind": "derivative",
        "source": source,
        "target": target,
        "requestDigest": _digest("9"),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"],
        "requestDigest": request["requestDigest"],
        "source": source,
        "derivative": target,
        "proof": {
            "tag": "mul",
            "p": {"tag": "variable"},
            "q": {"tag": "variable"},
        },
        "obligations": [],
        "claimsCompleteness": False,
    }
    return ExactCase("analytic_derivative", request["capability"], request, certificate)


def _cases() -> list[ExactCase]:
    return [
        _ideal_case(),
        _rational_case(),
        *_linear_cases(),
        _counterexample_case(),
        _formal_calculus_case(),
        _analytic_case(),
    ]


def _assert_policy(case: ExactCase) -> None:
    decision = decide_exact_kernel_replay(case.capability)
    if not decision.ok:
        raise RuntimeError(
            f"{case.name}: CR E2E case has unavailable exact policy: "
            f"{decision.code}: {decision.message}"
        )
    policy = load_assurance_policy(case.capability)
    cert = policy.get("certification") or {}
    if cert.get("crEligible") is not True:
        raise RuntimeError(f"{case.name}: release E2E case is not CR-eligible in registry")


def _lean_check(case: ExactCase, directory: Path) -> dict[str, Any]:
    _assert_policy(case)
    module = generate_module(
        capability_id=case.capability,
        request=case.request,
        certificate=case.certificate,
        candidate_bundle_digest=BUNDLE_DIGEST,
        module_name=f"MathEvidence.Generated.Replay.release_{case.name}",
        declaration_name=f"release_{case.name}",
    )
    metadata = verify(module)
    if not metadata.ok:
        raise RuntimeError(f"{case.name}: generated module metadata failed: {metadata.detail}")
    if "OfflineFixtures" in module.source_text:
        raise RuntimeError(f"{case.name}: generated exact source references OfflineFixtures")

    source = directory / f"{case.name}.lean"
    source.write_text(module.source_text, encoding="utf-8", newline="\n")
    result = run_bounded(
        ["lake", "env", "lean", str(source)],
        cwd=ROOT,
        limits=LIMITS,
    )
    if result.returncode != 0 or result.timed_out or result.output_truncated:
        raise RuntimeError(
            f"{case.name}: Lean candidate replay failed "
            f"(rc={result.returncode}, timeout={result.timed_out}, "
            f"truncated={result.output_truncated})\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return {
        "case": case.name,
        "capability": case.capability,
        "declaration": module.declaration_name,
        "sourceHash": module.source_hash,
        "generatorId": module.generator_id,
        "generatorVersion": module.generator_version,
        "grammarVersion": module.grammar_version,
        "requestDigest": module.request_digest,
        "candidateBundleDigest": module.candidate_bundle_digest,
        "leanWallTimeMs": result.wall_time_ms,
        "status": "lean_candidate_verified",
    }


def main() -> int:
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="mathevidence-exact-e2e-") as tmp:
        directory = Path(tmp)
        for case in _cases():
            result = _lean_check(case, directory)
            results.append(result)
            print(f"[exact-e2e] {case.name}: OK ({result['sourceHash']})")

    capabilities = {item["capability"] for item in results}
    expected = {
        "algebra.ideal_membership_witness",
        "algebra.rational_equality",
        "algebra.linear_algebra",
        "logic.finite_counterexample",
        "algebra.formal_rational_calculus",
        "analysis.analytic_calculus",
    }
    if capabilities != expected:
        raise RuntimeError(
            f"release exact E2E coverage mismatch: got {sorted(capabilities)}, "
            f"expected {sorted(expected)}"
        )

    print(json.dumps({"schemaVersion": "0.1.0", "results": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
