#!/usr/bin/env python3
"""Untrusted generator for Lean kernel-replay modules (Wave 2 / Wave 4).

This script MUST NOT be treated as theorem authority. Generated modules are
compiled by ``lake env lean``; generation/compile/axiom failures reject
certification.

Supports rational equality, linear algebra, finite counterexample, analytic,
and ideal-membership fixtures.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ALLOWED_AXIOMS_DEFAULT = (
    "propext",
    "Quot.sound",
    "Classical.choice",
    "Lean.ofReduceBool",
    "Lean.trustCompiler",
)


def _lean_string(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def _safe_ident(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    return cleaned


_FIXTURE_MODULES: dict[str, dict[str, str]] = {
    "basic_sympy": {
        "imports": (
            "import MathEvidence.Checkers.RationalEquality.OfflineFixtures\n"
            "import MathEvidence.Checkers.RationalEquality.ReplaySound"
        ),
        "open": (
            "open MathEvidence.Checkers.RationalEquality\n"
            "open MathEvidence.Checkers.RationalEquality.OfflineFixtures"
        ),
        "req": "req_basic_sympy",
        "cert": "cert_basic_sympy",
        "conclusion": "Claim.proposition req_basic_sympy.claim cert_basic_sympy.denomFactors",
        "proof": (
            "replaySound\n"
            "    req_basic_sympy\n"
            "    cert_basic_sympy\n"
            "    (by native_decide : checkBool req_basic_sympy cert_basic_sympy = true)"
        ),
    },
    "inv": {
        "imports": (
            "import MathEvidence.Checkers.LinearAlgebra.OfflineFixtures\n"
            "import MathEvidence.Checkers.LinearAlgebra.ReplaySound"
        ),
        "open": (
            "open MathEvidence.Checkers.LinearAlgebra\n"
            "open MathEvidence.Checkers.LinearAlgebra.OfflineFixtures"
        ),
        "req": "req_inv",
        "cert": "cert_inv",
        "conclusion": "Claim.proposition req_inv.claim cert_inv.inverse cert_inv.vector",
        "proof": (
            "replaySound\n"
            "    req_inv\n"
            "    cert_inv\n"
            "    (by native_decide : checkBool req_inv cert_inv = true)"
        ),
    },
    "sys": {
        "imports": (
            "import MathEvidence.Checkers.LinearAlgebra.OfflineFixtures\n"
            "import MathEvidence.Checkers.LinearAlgebra.ReplaySound"
        ),
        "open": (
            "open MathEvidence.Checkers.LinearAlgebra\n"
            "open MathEvidence.Checkers.LinearAlgebra.OfflineFixtures"
        ),
        "req": "req_sys",
        "cert": "cert_sys",
        "conclusion": "Claim.proposition req_sys.claim cert_sys.inverse cert_sys.vector",
        "proof": (
            "replaySound\n"
            "    req_sys\n"
            "    cert_sys\n"
            "    (by native_decide : checkBool req_sys cert_sys = true)"
        ),
    },
    "ker": {
        "imports": (
            "import MathEvidence.Checkers.LinearAlgebra.OfflineFixtures\n"
            "import MathEvidence.Checkers.LinearAlgebra.ReplaySound"
        ),
        "open": (
            "open MathEvidence.Checkers.LinearAlgebra\n"
            "open MathEvidence.Checkers.LinearAlgebra.OfflineFixtures"
        ),
        "req": "req_ker",
        "cert": "cert_ker",
        "conclusion": "Claim.proposition req_ker.claim cert_ker.inverse cert_ker.vector",
        "proof": (
            "replaySound\n"
            "    req_ker\n"
            "    cert_ker\n"
            "    (by native_decide : checkBool req_ker cert_ker = true)"
        ),
    },
    "det": {
        "imports": (
            "import MathEvidence.Checkers.LinearAlgebra.OfflineFixtures\n"
            "import MathEvidence.Checkers.LinearAlgebra.ReplaySound"
        ),
        "open": (
            "open MathEvidence.Checkers.LinearAlgebra\n"
            "open MathEvidence.Checkers.LinearAlgebra.OfflineFixtures"
        ),
        "req": "req_det",
        "cert": "cert_det",
        "conclusion": "Claim.proposition req_det.claim cert_det.inverse cert_det.vector",
        "proof": (
            "replaySound\n"
            "    req_det\n"
            "    cert_det\n"
            "    (by native_decide : checkBool req_det cert_det = true)"
        ),
    },
    "nat_eq0": {
        "imports": (
            "import MathEvidence.Checkers.Counterexample.OfflineFixtures\n"
            "import MathEvidence.Checkers.Counterexample.ReplaySound"
        ),
        "open": (
            "open MathEvidence.Checkers.Counterexample\n"
            "open MathEvidence.Checkers.Counterexample.OfflineFixtures"
        ),
        "req": "req_nat_eq0",
        "cert": "cert_nat_eq0",
        "conclusion": "Claim.proposition req_nat_eq0.claim cert_nat_eq0.witness",
        "proof": (
            "replaySound\n"
            "    req_nat_eq0\n"
            "    cert_nat_eq0\n"
            "    (by native_decide : checkBool req_nat_eq0 cert_nat_eq0 = true)"
        ),
    },
    "bool_false": {
        "imports": (
            "import MathEvidence.Checkers.Counterexample.OfflineFixtures\n"
            "import MathEvidence.Checkers.Counterexample.ReplaySound"
        ),
        "open": (
            "open MathEvidence.Checkers.Counterexample\n"
            "open MathEvidence.Checkers.Counterexample.OfflineFixtures"
        ),
        "req": "req_bool",
        "cert": "cert_bool",
        "conclusion": "Claim.proposition req_bool.claim cert_bool.witness",
        "proof": (
            "replaySound\n"
            "    req_bool\n"
            "    cert_bool\n"
            "    (by native_decide : checkBool req_bool cert_bool = true)"
        ),
    },
    "cert_product": {
        "imports": (
            "import MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures\n"
            "import MathEvidence.Checkers.AnalyticCalculus.ReplaySound"
        ),
        "open": (
            "open MathEvidence.Checkers.AnalyticCalculus\n"
            "open MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures"
        ),
        "req": "cert_product",
        "cert": "cert_product",
        "conclusion": (
            "HasDerivAt cert_product.source.interpret "
            "(cert_product.derivative.interpret x) x"
        ),
        "proof": (
            "certified_analytic_replay_product x"
        ),
    },
    "xy": {
        "imports": (
            "import MathEvidence.Checkers.IdealMembership.OfflineFixtures\n"
            "import MathEvidence.Checkers.IdealMembership.ReplaySound"
        ),
        "open": (
            "open MathEvidence.Checkers.IdealMembership\n"
            "open MathEvidence.Checkers.IdealMembership.OfflineFixtures"
        ),
        "req": "req_xy",
        "cert": "cert_xy",
        "conclusion": "Claim.proposition req_xy.claim",
        "proof": (
            "replaySound\n"
            "    req_xy\n"
            "    cert_xy\n"
            "    (by native_decide : checkBool req_xy cert_xy = true)"
        ),
    },
    "x2m1": {
        "imports": (
            "import MathEvidence.Checkers.IdealMembership.OfflineFixtures\n"
            "import MathEvidence.Checkers.IdealMembership.ReplaySound"
        ),
        "open": (
            "open MathEvidence.Checkers.IdealMembership\n"
            "open MathEvidence.Checkers.IdealMembership.OfflineFixtures"
        ),
        "req": "req_x2m1",
        "cert": "cert_x2m1",
        "conclusion": "Claim.proposition req_x2m1.claim",
        "proof": (
            "replaySound\n"
            "    req_x2m1\n"
            "    cert_x2m1\n"
            "    (by native_decide : checkBool req_x2m1 cert_x2m1 = true)"
        ),
    },
}


def generate_module(
    *,
    module_name: str,
    declaration_name: str,
    theorem_type: str,
    request_digest: str,
    candidate_bundle_digest: str,
    fixture: str = "basic_sympy",
    check_bool_proof: str = "by native_decide",
) -> str:
    """Generate a Lean module that applies ``replaySound`` for a fixture."""
    del check_bool_proof  # fixture templates embed their own checkBool proofs
    decl = _safe_ident(declaration_name)
    fx = _FIXTURE_MODULES.get(fixture) or _FIXTURE_MODULES["basic_sympy"]
    return f"""/-
AUTO-GENERATED by scripts/generate_replay_module.py — UNTRUSTED generator.
Authority is Lean kernel acceptance of the declaration below + axiom policy.
theoremType = {theorem_type}
-/
{fx["imports"]}

namespace {_safe_ident(module_name.split(".")[-1])}

{fx["open"]}

/-- Generated kernel-replay certificate binding.
candidateBundleDigest = {candidate_bundle_digest}
requestDigest = {request_digest}
-/
theorem {decl} :
    {fx["conclusion"]} :=
  {fx["proof"]}

#print axioms {decl}

end {_safe_ident(module_name.split(".")[-1])}
"""


def generate_from_target(target: dict[str, Any], *, fixture: str | None = None) -> str:
    """Generate module from a ReplayTarget JSON object."""
    fx = fixture or str(target.get("fixture") or "basic_sympy")
    cap = str(target.get("capability") or "")
    if fixture is None:
        if cap == "algebra.linear_algebra":
            fx = str(target.get("fixture") or "inv")
        elif cap == "logic.finite_counterexample":
            fx = str(target.get("fixture") or "nat_eq0")
        elif cap == "analysis.analytic_calculus":
            fx = "cert_product"
        elif cap == "algebra.ideal_membership_witness":
            fx = str(target.get("fixture") or "xy")
    if fx == "cert_product":
        # Analytic fixture needs an explicit ℝ binder in the theorem type.
        decl = _safe_ident(str(target["declarationName"]))
        module_name = str(target["moduleName"])
        return f"""/-
AUTO-GENERATED by scripts/generate_replay_module.py — UNTRUSTED generator.
Authority is Lean kernel acceptance of the declaration below + axiom policy.
theoremType = {target.get("theoremTypeCanonical", "HasDerivAt ...")}
-/
import MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures
import MathEvidence.Checkers.AnalyticCalculus.ReplaySound

namespace {_safe_ident(module_name.split(".")[-1])}

open MathEvidence.Checkers.AnalyticCalculus
open MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures

/-- Generated kernel-replay certificate binding.
candidateBundleDigest = {target.get("candidateBundleDigest") or target["requestDigest"]}
requestDigest = {target["requestDigest"]}
-/
theorem {decl} (x : ℝ) :
    HasDerivAt cert_product.source.interpret
      (cert_product.derivative.interpret x) x :=
  certified_analytic_replay_product x

#print axioms {decl}

end {_safe_ident(module_name.split(".")[-1])}
"""
    return generate_module(
        module_name=str(target["moduleName"]),
        declaration_name=str(target["declarationName"]),
        theorem_type=str(target["theoremTypeCanonical"]),
        request_digest=str(target["requestDigest"]),
        candidate_bundle_digest=str(
            target.get("candidateBundleDigest") or target["requestDigest"]
        ),
        fixture=fx,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, help="replay-target.cjson path")
    parser.add_argument("--out", type=Path, required=True, help="output .lean path")
    parser.add_argument(
        "--declaration-name",
        default="certified_replay",
        help="declaration name when --target is omitted",
    )
    parser.add_argument(
        "--module-name",
        default="MathEvidence.Generated.Replay.Scratch",
        help="module name when --target is omitted",
    )
    parser.add_argument(
        "--fixture",
        default="basic_sympy",
        choices=sorted(_FIXTURE_MODULES),
        help="offline fixture key",
    )
    args = parser.parse_args()
    if args.target is not None:
        target = json.loads(args.target.read_text(encoding="utf-8"))
        text = generate_from_target(target, fixture=args.fixture)
    else:
        text = generate_module(
            module_name=args.module_name,
            declaration_name=args.declaration_name,
            theorem_type="forall (x : Rat), x + 0 = x",
            request_digest="sha256:" + ("0" * 64),
            candidate_bundle_digest="sha256:" + ("0" * 64),
            fixture=args.fixture,
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8", newline="\n")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
