"""Release gate: execute every CR-eligible production exact form with pinned Lean.

This is a CI/release proof-of-execution gate, not a second verifier.
Coverage is derived from the machine-readable maturity inventory and production
plugin operation/whitelist constants. A newly promoted capability or theorem
form therefore fails this gate until a candidate-specific Lean E2E case exists.
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
from adapters.common.exact_replay.plugins.analytic_calculus import WHITELIST_KINDS
from adapters.common.exact_replay.plugins.formal_rational_calculus import (
    OPERATIONS as FORMAL_OPERATIONS,
)
from adapters.common.exact_replay.plugins.linear_algebra import OPERATIONS as LA_OPERATIONS
from adapters.common.limits import ResourceLimits
from agent.api.assurance_policy import decide_exact_kernel_replay, load_assurance_policy

ROOT = Path(__file__).resolve().parents[2]
BUNDLE_DIGEST = "sha256:" + ("c" * 64)
LIMITS = ResourceLimits(max_wall_time_ms=180_000, max_output_bytes=4_194_304)
INVENTORY = ROOT / "registry" / "maturity-inventory.json"


@dataclass(frozen=True)
class ExactCase:
    name: str
    capability: str
    form: str
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


def _provenance() -> dict[str, str]:
    return {"backendId": "release-e2e", "adapterVersion": "0.1.0"}


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
        "multipliers": [_poly(2, 1, [0, 1]), {"varCount": 2, "terms": []}],
        "claimClass": "witness",
    }
    return ExactCase("ideal_membership", request["capability"], "witness", request, certificate)


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
        "provenance": _provenance(),
    }
    return ExactCase("rational_equality", request["capability"], "soundResult", request, certificate)


def _linear_cases() -> list[ExactCase]:
    base = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
    }
    cases: list[ExactCase] = []

    request = {
        **base,
        "operation": "inverse_witness",
        "matrix": _matrix([[("2", "1")]]),
        "requestedClaim": "witness",
        "requestDigest": _digest("3"),
    }
    cert = {
        "schemaVersion": "0.1.0", "capability": base["capability"],
        "capabilityVersion": base["capabilityVersion"], "requestDigest": request["requestDigest"],
        "operation": "inverse_witness", "inverse": _matrix([[("1", "2")]]),
        "provenance": _provenance(),
    }
    cases.append(ExactCase("linear_inverse", base["capability"], "inverse_witness", request, cert))

    request = {
        **base, "operation": "system_solution", "matrix": _matrix([[("2", "1")]]),
        "rhs": [_rat("4")], "requestedClaim": "witness", "requestDigest": _digest("4"),
    }
    cert = {
        "schemaVersion": "0.1.0", "capability": base["capability"],
        "capabilityVersion": base["capabilityVersion"], "requestDigest": request["requestDigest"],
        "operation": "system_solution", "vector": [_rat("2")], "provenance": _provenance(),
    }
    cases.append(ExactCase("linear_system", base["capability"], "system_solution", request, cert))

    request = {
        **base, "operation": "kernel_vector",
        "matrix": _matrix([[("1", "1"), ("1", "1")], [("2", "1"), ("2", "1")]]),
        "requestedClaim": "witness", "requestDigest": _digest("5"),
    }
    cert = {
        "schemaVersion": "0.1.0", "capability": base["capability"],
        "capabilityVersion": base["capabilityVersion"], "requestDigest": request["requestDigest"],
        "operation": "kernel_vector", "vector": [_rat("1"), _rat("-1")],
        "provenance": _provenance(),
    }
    cases.append(ExactCase("linear_kernel", base["capability"], "kernel_vector", request, cert))

    request = {
        **base, "operation": "det_identity",
        "matrix": _matrix([[("1", "1"), ("2", "1")], [("3", "1"), ("4", "1")]]),
        "claimedDet": _rat("-2"), "requestedClaim": "soundResult", "requestDigest": _digest("6"),
    }
    cert = {
        "schemaVersion": "0.1.0", "capability": base["capability"],
        "capabilityVersion": base["capabilityVersion"], "requestDigest": request["requestDigest"],
        "operation": "det_identity", "provenance": _provenance(),
    }
    cases.append(ExactCase("linear_determinant", base["capability"], "det_identity", request, cert))
    return cases


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
        "provenance": _provenance(),
    }
    return ExactCase("finite_counterexample", request["capability"], "refutation", request, certificate)


def _formal_base(operation: str, digest_char: str) -> tuple[dict[str, Any], dict[str, Any]]:
    request: dict[str, Any] = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.formal_rational_calculus",
        "capabilityVersion": "0.1.0",
        "operation": operation,
        "variables": [{"name": "x", "type": "Rat"}],
        "independentVar": "x",
        "expr": {"tag": "var", "name": "x"},
        "candidate": {"tag": "int", "value": "1"},
        "domainConditions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": _digest(digest_char),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"],
        "requestDigest": request["requestDigest"],
        "operation": operation,
        "domainConditions": [],
        "provenance": _provenance(),
    }
    return request, certificate


def _formal_cases() -> list[ExactCase]:
    cases: list[ExactCase] = []

    req, cert = _formal_base("derivative_candidate", "8")
    req["expr"] = {"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2}
    req["candidate"] = {
        "tag": "mul", "left": {"tag": "int", "value": "2"},
        "right": {"tag": "var", "name": "x"},
    }
    cases.append(ExactCase("formal_derivative", req["capability"], "derivative_candidate", req, cert))

    req, cert = _formal_base("antiderivative_candidate", "9")
    req["expr"] = {"tag": "var", "name": "x"}
    req["candidate"] = {
        "tag": "mul",
        "left": {"tag": "rat", "num": "1", "den": "2"},
        "right": {"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
    }
    cases.append(ExactCase("formal_antiderivative", req["capability"], "antiderivative_candidate", req, cert))

    req, cert = _formal_base("recurrence_identity", "a")
    req["variables"] = [{"name": "n", "type": "Rat"}, {"name": "u", "type": "Rat"}]
    req["independentVar"] = "n"
    req["dependentVar"] = "u"
    req["expr"] = {"tag": "var", "name": "n"}
    req["candidate"] = {"tag": "int", "value": "0"}
    req["recurrenceRhs"] = {
        "tag": "add",
        "left": {"tag": "var", "name": "u"},
        "right": {"tag": "int", "value": "1"},
    }
    cases.append(ExactCase("formal_recurrence", req["capability"], "recurrence_identity", req, cert))

    req, cert = _formal_base("ode_candidate", "b")
    req["variables"] = [{"name": "x", "type": "Rat"}, {"name": "y", "type": "Rat"}]
    req["dependentVar"] = "y"
    req["expr"] = {"tag": "var", "name": "x"}
    req["candidate"] = {"tag": "int", "value": "0"}
    req["odeRhs"] = {"tag": "int", "value": "1"}
    req["initialConditions"] = [
        {"point": {"tag": "int", "value": "0"}, "value": {"tag": "int", "value": "0"}}
    ]
    cases.append(ExactCase("formal_ode", req["capability"], "ode_candidate", req, cert))
    return cases


def _analytic_derivative_case(kind: str, digest_char: str) -> ExactCase:
    source = {
        "tag": "mul",
        "lhs": {"tag": "variable", "idx": 0},
        "rhs": {"tag": "variable", "idx": 0},
    }
    target = {
        "tag": "add",
        "lhs": {
            "tag": "mul", "lhs": {"tag": "const", "value": "1"},
            "rhs": {"tag": "variable", "idx": 0},
        },
        "rhs": {
            "tag": "mul", "lhs": {"tag": "variable", "idx": 0},
            "rhs": {"tag": "const", "value": "1"},
        },
    }
    request = {
        "schemaVersion": "0.1.0", "capability": "analysis.analytic_calculus",
        "capabilityVersion": "0.1.0", "kind": kind, "source": source, "target": target,
        "requestDigest": _digest(digest_char),
    }
    certificate = {
        "schemaVersion": "0.1.0", "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"], "requestDigest": request["requestDigest"],
        "source": source, "derivative": target,
        "proof": {"tag": "mul", "p": {"tag": "variable"}, "q": {"tag": "variable"}},
        "obligations": [], "claimsCompleteness": False,
    }
    return ExactCase(f"analytic_{kind}", request["capability"], kind, request, certificate)


def _analytic_cases() -> list[ExactCase]:
    cases = [
        _analytic_derivative_case("derivative", "c"),
        _analytic_derivative_case("derivativeWithin", "d"),
    ]
    request = {
        "schemaVersion": "0.1.0", "capability": "analysis.analytic_calculus",
        "capabilityVersion": "0.1.0", "kind": "antiderivative",
        "source": {"tag": "variable", "idx": 0},
        "target": {"tag": "const", "value": "1"},
        "requestDigest": _digest("e"),
    }
    certificate = {
        "schemaVersion": "0.1.0", "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"], "requestDigest": request["requestDigest"],
        "source": request["source"], "derivative": request["target"],
        "proof": {"tag": "variable"}, "obligations": [], "claimsCompleteness": False,
    }
    cases.append(ExactCase("analytic_antiderivative", request["capability"], "antiderivative", request, certificate))

    request = {
        "schemaVersion": "0.1.0", "capability": "analysis.analytic_calculus",
        "capabilityVersion": "0.1.0", "kind": "odeCandidate",
        "source": {"tag": "variable", "idx": 0},
        "target": {"tag": "const", "value": "1"},
        "initialConditions": [
            {"point": {"tag": "const", "value": "0"}, "value": {"tag": "const", "value": "0"}}
        ],
        "requestDigest": _digest("f"),
    }
    certificate = {
        "schemaVersion": "0.1.0", "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"], "requestDigest": request["requestDigest"],
        "solution": {"tag": "variable", "idx": 0}, "rhs": {"tag": "const", "value": "1"},
        "derivProof": {"tag": "variable"}, "initialConditions": request["initialConditions"],
        "obligations": [], "claimsCompleteness": False,
    }
    cases.append(ExactCase("analytic_ode", request["capability"], "odeCandidate", request, certificate))
    return cases


def _cases() -> list[ExactCase]:
    return [
        _ideal_case(),
        _rational_case(),
        *_linear_cases(),
        _counterexample_case(),
        *_formal_cases(),
        *_analytic_cases(),
    ]


def _inventory_cr_eligible() -> set[str]:
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    return {
        str(entry["id"])
        for entry in data.get("capabilities") or []
        if isinstance(entry, dict) and entry.get("cr_eligible") is True
    }


def _assert_coverage(cases: list[ExactCase]) -> None:
    capabilities = {case.capability for case in cases}
    expected_capabilities = _inventory_cr_eligible()
    if capabilities != expected_capabilities:
        raise RuntimeError(
            "release exact E2E capability coverage mismatch: "
            f"got {sorted(capabilities)}, expected inventory {sorted(expected_capabilities)}"
        )

    forms_by_cap: dict[str, set[str]] = {}
    for case in cases:
        forms_by_cap.setdefault(case.capability, set()).add(case.form)

    expected_forms = {
        "algebra.linear_algebra": set(LA_OPERATIONS),
        "algebra.formal_rational_calculus": set(FORMAL_OPERATIONS),
        "analysis.analytic_calculus": set(WHITELIST_KINDS),
    }
    for capability, expected in expected_forms.items():
        got = forms_by_cap.get(capability, set())
        if got != expected:
            raise RuntimeError(
                f"{capability}: exact theorem-form E2E coverage mismatch: "
                f"got {sorted(got)}, production enables {sorted(expected)}"
            )


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
        "form": case.form,
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
    cases = _cases()
    _assert_coverage(cases)

    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="mathevidence-exact-e2e-") as tmp:
        directory = Path(tmp)
        for case in cases:
            result = _lean_check(case, directory)
            results.append(result)
            print(
                f"[exact-e2e] {case.capability}::{case.form}: "
                f"OK ({result['sourceHash']})"
            )

    print(json.dumps({"schemaVersion": "0.2.0", "results": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
