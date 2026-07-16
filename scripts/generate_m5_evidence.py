#!/usr/bin/env python3
"""Generate Milestone 5 symbolic calculus evidence fixtures."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import write_bundle  # noqa: E402
from adapters.common.canonical import bind_request_digest  # noqa: E402
from adapters.common.limits import ResourceLimits, ResourceTracker  # noqa: E402
from adapters.sympy.adapter import compute_symbolic_calculus  # noqa: E402

CAP = "analysis.symbolic_calculus"
CAP_VER = "0.1.0"


def _base(**extra: object) -> dict:
    req: dict = {
        "schemaVersion": "0.1.0",
        "capability": CAP,
        "capabilityVersion": CAP_VER,
        "requestedClaim": "candidate",
        "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        **extra,
    }
    return bind_request_digest(req)


def write_case(name: str, request: dict, readme: str, *, example: bool = True) -> None:
    result = compute_symbolic_calculus(request, ResourceTracker(ResourceLimits())).result
    out_dirs = []
    if example:
        out_dirs.append(ROOT / "evidence" / "examples" / name)
    conf = ROOT / "evidence" / "conformance" / "symbolic_calculus" / name / "bundle"
    out_dirs.append(conf)
    for out in out_dirs:
        if out.exists():
            shutil.rmtree(out)
        write_bundle(
            out,
            request=request,
            candidate=result["candidate"],
            certificate=result["certificate"],
            result_status="computed",
            claim_class="candidate",
            readme=readme,
        )
        print(f"wrote {out.relative_to(ROOT)}")


def main() -> int:
    # d/dx(x^2) = 2x
    write_case(
        "calculus_derivative_x2",
        _base(
            operation="derivative_candidate",
            variables=[{"name": "x", "type": "Rat"}],
            independentVar="x",
            expr={"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
            candidate={
                "tag": "mul",
                "left": {"tag": "int", "value": "2"},
                "right": {"tag": "var", "name": "x"},
            },
            domainConditions=[],
        ),
        "# Derivative candidate\n\n`d/dx(x^2) = 2x` (formal identity; not completeness).\n",
    )

    # antiderivative: F=x^2, f=2x
    write_case(
        "calculus_antiderivative_x2",
        _base(
            operation="antiderivative_candidate",
            variables=[{"name": "x", "type": "Rat"}],
            independentVar="x",
            expr={
                "tag": "mul",
                "left": {"tag": "int", "value": "2"},
                "right": {"tag": "var", "name": "x"},
            },
            candidate={"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
            domainConditions=[],
        ),
        "# Antiderivative candidate\n\n`F'=f` for `F=x^2`, `f=2x`. Completeness not claimed.\n",
    )

    # recurrence u(n)=n, u(n+1)=u+1
    write_case(
        "calculus_recurrence_n",
        _base(
            operation="recurrence_identity",
            variables=[{"name": "n", "type": "Rat"}, {"name": "u", "type": "Rat"}],
            independentVar="n",
            dependentVar="u",
            expr={"tag": "var", "name": "n"},
            candidate={"tag": "int", "value": "0"},
            recurrenceRhs={
                "tag": "add",
                "left": {"tag": "var", "name": "u"},
                "right": {"tag": "int", "value": "1"},
            },
            domainConditions=[],
        ),
        "# Recurrence identity\n\nClosed form `u(n)=n` satisfies `u(n+1)=u+1`. Uniqueness not claimed.\n",
    )

    # ODE y'=1, y=x, y(0)=0
    write_case(
        "calculus_ode_y_eq_x",
        _base(
            operation="ode_candidate",
            variables=[{"name": "x", "type": "Rat"}, {"name": "y", "type": "Rat"}],
            independentVar="x",
            dependentVar="y",
            expr={"tag": "var", "name": "x"},
            candidate={"tag": "int", "value": "0"},
            odeRhs={"tag": "int", "value": "1"},
            initialConditions=[
                {
                    "point": {"tag": "int", "value": "0"},
                    "value": {"tag": "int", "value": "0"},
                }
            ],
            domainConditions=[],
        ),
        "# ODE candidate\n\n`y'=1` with solution `y=x` and IC `y(0)=0`. Uniqueness not claimed.\n",
    )

    # Mathematica offline fixture (same derivative case, mathematica provenance)
    deriv_req = _base(
        operation="derivative_candidate",
        variables=[{"name": "x", "type": "Rat"}],
        independentVar="x",
        expr={"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
        candidate={
            "tag": "mul",
            "left": {"tag": "int", "value": "2"},
            "right": {"tag": "var", "name": "x"},
        },
        domainConditions=[],
    )
    result = compute_symbolic_calculus(deriv_req, ResourceTracker(ResourceLimits())).result
    cert = dict(result["certificate"])
    cert["provenance"] = {
        "backendId": "mathematica",
        "backendVersion": "fixture",
        "adapterVersion": "0.1.0",
        "leanLinkVersion": None,
        "generatedAt": cert["provenance"]["generatedAt"],
        "deterministic": True,
    }
    cert["notes"] = "Offline Mathematica fixture; live wolframscript optional."
    out = ROOT / "evidence" / "examples" / "calculus_derivative_mathematica_offline"
    if out.exists():
        shutil.rmtree(out)
    write_bundle(
        out,
        request=deriv_req,
        candidate=result["candidate"],
        certificate=cert,
        result_status="computed",
        claim_class="candidate",
        readme="# Mathematica offline calculus fixture\n\nReplay without Wolfram Language.\n",
    )
    print(f"wrote {out.relative_to(ROOT)}")

    # Conformance README
    conf_root = ROOT / "evidence" / "conformance" / "symbolic_calculus"
    conf_root.mkdir(parents=True, exist_ok=True)
    (conf_root / "README.md").write_text(
        "# Symbolic calculus conformance\n\n"
        "Milestone 5 candidate checks. Domain/singularity conditions are always explicit.\n"
        "Candidate validity never implies completeness.\n",
        encoding="utf-8",
    )
    print("ok generate_m5_evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
