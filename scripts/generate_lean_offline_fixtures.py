#!/usr/bin/env python3
"""Generate Lean offline-replay fixtures from committed evidence bundles.

Writes MathEvidence/Checkers/RationalEquality/OfflineFixtures.lean so Lake CI
replays SymPy + Mathematica evidence without starting backends.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "MathEvidence" / "Checkers" / "RationalEquality" / "OfflineFixtures.lean"

# Bundles that must accept (poly + cover + digest).
ACCEPT = [
    ("basic_sympy", ROOT / "evidence" / "examples" / "rational_equality_basic"),
    (
        "basic_mathematica",
        ROOT / "evidence" / "examples" / "rational_equality_mathematica_offline",
    ),
    (
        "valid_identity",
        ROOT / "evidence" / "conformance" / "rfc0001" / "valid_identity" / "bundle",
    ),
    (
        "redundant_condition",
        ROOT / "evidence" / "conformance" / "rfc0001" / "redundant_condition" / "bundle",
    ),
    (
        "variable_permutation",
        ROOT / "evidence" / "conformance" / "rfc0001" / "variable_permutation" / "bundle",
    ),
    (
        "large_coeffs",
        ROOT / "evidence" / "conformance" / "rfc0001" / "large_coeffs" / "bundle",
    ),
]

# Bundles that must reject.
REJECT = [
    (
        "false_identity",
        ROOT / "evidence" / "conformance" / "rfc0001" / "false_identity" / "bundle",
    ),
    (
        "hash_mismatch",
        ROOT / "evidence" / "conformance" / "rfc0001" / "hash_mismatch" / "bundle",
    ),
]


def lean_int(s: str) -> str:
    n = int(s)
    if n < 0:
        return f"(-{abs(n)})"
    return str(n)


def emit_expr(node: dict, names: list[str]) -> str:
    tag = node["tag"]
    if tag == "var":
        idx = names.index(node["name"])
        return f"Expr.var {idx}"
    if tag == "int":
        return f"Expr.int ({lean_int(node['value'])} : Int)"
    if tag == "rat":
        return f"Expr.rat ({lean_int(node['n'])} : Int) {int(node['d'])}"
    if tag == "neg":
        arg = node.get("arg", node.get("e"))
        return f"Expr.neg ({emit_expr(arg, names)})"
    if tag in {"add", "sub", "mul"}:
        return (
            f"Expr.{tag} ({emit_expr(node['left'], names)}) "
            f"({emit_expr(node['right'], names)})"
        )
    if tag == "pow":
        exp = node.get("exp", node.get("k"))
        return f"Expr.pow ({emit_expr(node['base'], names)}) {int(exp)}"
    if tag == "div":
        return (
            f"Expr.div ({emit_expr(node['num'], names)}) "
            f"({emit_expr(node['den'], names)})"
        )
    raise ValueError(f"unsupported tag {tag!r}")


def load_bundle(path: Path) -> tuple[dict, dict]:
    req = json.loads((path / "request.json").read_text(encoding="utf-8"))
    cert = json.loads((path / "certificate.json").read_text(encoding="utf-8"))
    return req, cert


def emit_claim(req: dict) -> str:
    names = [v["name"] for v in req["variables"]]
    names_lit = ", ".join(f'"{n}"' for n in names)
    lhs = emit_expr(req["lhs"], names)
    rhs = emit_expr(req["rhs"], names)
    return "\n".join(
        [
            "  {",
            f"    varNames := [{names_lit}]",
            f"    lhs := {lhs}",
            f"    rhs := {rhs}",
            "  }",
        ]
    )


def emit_factors(cert: dict, names: list[str]) -> str:
    factors = []
    for entry in cert.get("denominatorFactors", []):
        expr = entry["expr"] if isinstance(entry, dict) and "expr" in entry else entry
        factors.append(emit_expr(expr, names))
    if not factors:
        return "[]"
    return "[" + ", ".join(factors) + "]"


def emit_fixture(ident: str, path: Path, expect_accept: bool) -> str:
    req, cert = load_bundle(path)
    names = [v["name"] for v in req["variables"]]
    digest = req["requestDigest"]
    cert_digest = cert["requestDigest"]
    # Lean checks request↔certificate binding. The committed hash_mismatch
    # fixture uses a shared bogus digest (Python detects payload recompute
    # failure); force a Lean-visible mismatch for the shared checker.
    if ident == "hash_mismatch":
        cert_digest = (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000"
        )
    claim = emit_claim(req)
    factors = emit_factors(cert, names)
    lines = [
        f"/-- Generated from `{path.relative_to(ROOT).as_posix()}`. -/",
        f"def claim_{ident} : Claim :=",
        claim,
        f"def digest_{ident} : RequestDigest := ⟨\"{digest}\"⟩",
        f"def req_{ident} : Request :=",
        "  { claim := claim_" + ident + ", requestDigest := digest_" + ident + " }",
        f"def cert_{ident} : Certificate where",
        f"  requestDigest := ⟨\"{cert_digest}\"⟩",
        f"  denomFactors := {factors}",
        f"def bundle_{ident} : ReplayBundle where",
        f"  request := req_{ident}",
        f"  certificate := cert_{ident}",
    ]
    if expect_accept:
        lines += [
            f"theorem replay_{ident} :",
            f"    checkBool req_{ident} cert_{ident} = true := by native_decide",
            f"theorem replay_report_{ident} :",
            f"    (replay bundle_{ident}).accepted = true := by native_decide",
            f"theorem sound_{ident} :",
            f"    Claim.proposition claim_{ident} cert_{ident}.denomFactors :=",
            f"  checkBool_sound req_{ident} cert_{ident} replay_{ident}",
        ]
    else:
        lines += [
            f"theorem reject_{ident} :",
            f"    checkBool req_{ident} cert_{ident} = false := by native_decide",
            f"theorem reject_report_{ident} :",
            f"    (replay bundle_{ident}).accepted = false := by native_decide",
        ]
    return "\n".join(lines)


def main() -> int:
    parts = [
        "/-",
        "Copyright (c) 2026 MathEvidence contributors. All rights reserved.",
        "Released under Apache 2.0 license as described in the file LICENSE.",
        "Authors: MathEvidence contributors",
        "-/",
        "import MathEvidence.Checkers.RationalEquality.Check",
        "import MathEvidence.Checkers.RationalEquality.Replay",
        "import MathEvidence.Checkers.RationalEquality.Soundness",
        "import MathEvidence.IR.RationalExpr.Syntax",
        "",
        "/-",
        "AUTO-GENERATED by `scripts/generate_lean_offline_fixtures.py`.",
        "Do not edit by hand; regenerate after evidence bundle changes.",
        "-/",
        "",
        "namespace MathEvidence.Checkers.RationalEquality.OfflineFixtures",
        "",
        "open MathEvidence.Core",
        "open MathEvidence.IR.RationalExpr",
        "open MathEvidence.Checkers.RationalEquality",
        "",
    ]
    for ident, path in ACCEPT:
        parts.append(emit_fixture(ident, path, True))
        parts.append("")
    for ident, path in REJECT:
        parts.append(emit_fixture(ident, path, False))
        parts.append("")
    parts.append("end MathEvidence.Checkers.RationalEquality.OfflineFixtures")
    parts.append("")
    OUT.write_text("\n".join(parts), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(ACCEPT)} accept, {len(REJECT)} reject)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
