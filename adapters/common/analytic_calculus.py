"""Analytic calculus adapter helpers (ME-RV-054).

Proposes AnalyticExpr + DerivProof trees. Lean reconstructs and checks the tree;
this module never asserts HasDerivAt. Domain obligations are listed explicitly —
never as trusted Booleans.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CAPABILITY_ID = "analysis.analytic_calculus"
CAPABILITY_VERSION = "0.1.0"

ExprDict = dict[str, Any]
ProofDict = dict[str, Any]
ObligationDict = dict[str, Any]


class AnalyticError(ValueError):
    """Malformed analytic IR / certificate."""


def _tag(e: ExprDict) -> str:
    if "tag" not in e:
        raise AnalyticError("expression missing tag")
    return str(e["tag"])


def expr_size(e: ExprDict) -> int:
    t = _tag(e)
    if t in ("variable", "const"):
        return 1
    if t in ("add", "sub", "mul", "div"):
        return 1 + expr_size(e["lhs"]) + expr_size(e["rhs"])
    if t == "pow":
        return 1 + expr_size(e["base"])
    if t in ("inv", "neg", "sin", "cos", "exp", "log"):
        return 1 + expr_size(e["arg"])
    raise AnalyticError(f"unknown expression tag {t!r}")


def is_univariate(e: ExprDict) -> bool:
    t = _tag(e)
    if t == "variable":
        return int(e["idx"]) == 0
    if t == "const":
        return True
    if t in ("add", "sub", "mul", "div"):
        return is_univariate(e["lhs"]) and is_univariate(e["rhs"])
    if t == "pow":
        return is_univariate(e["base"])
    if t in ("inv", "neg", "sin", "cos", "exp", "log"):
        return is_univariate(e["arg"])
    raise AnalyticError(f"unknown expression tag {t!r}")


def reconstruct_deriv(source: ExprDict, proof: ProofDict) -> ExprDict | None:
    """Mirror Lean `reconstructDeriv` (syntax only)."""
    pt = str(proof.get("tag", ""))
    st = _tag(source)

    if st == "variable" and int(source["idx"]) == 0 and pt == "variable":
        return {"tag": "const", "value": "1"}
    if st == "const" and pt == "const":
        return {"tag": "const", "value": "0"}
    if st == "neg" and pt == "neg":
        da = reconstruct_deriv(source["arg"], proof["p"])
        return None if da is None else {"tag": "neg", "arg": da}
    if st == "add" and pt == "add":
        da = reconstruct_deriv(source["lhs"], proof["p"])
        db = reconstruct_deriv(source["rhs"], proof["q"])
        if da is None or db is None:
            return None
        return {"tag": "add", "lhs": da, "rhs": db}
    if st == "sub" and pt == "sub":
        da = reconstruct_deriv(source["lhs"], proof["p"])
        db = reconstruct_deriv(source["rhs"], proof["q"])
        if da is None or db is None:
            return None
        return {"tag": "sub", "lhs": da, "rhs": db}
    if st == "mul" and pt == "mul":
        da = reconstruct_deriv(source["lhs"], proof["p"])
        db = reconstruct_deriv(source["rhs"], proof["q"])
        if da is None or db is None:
            return None
        return {
            "tag": "add",
            "lhs": {"tag": "mul", "lhs": da, "rhs": source["rhs"]},
            "rhs": {"tag": "mul", "lhs": source["lhs"], "rhs": db},
        }
    if st == "inv" and pt == "inv":
        da = reconstruct_deriv(source["arg"], proof["p"])
        if da is None:
            return None
        aa = {"tag": "mul", "lhs": source["arg"], "rhs": source["arg"]}
        return {"tag": "neg", "arg": {"tag": "div", "lhs": da, "rhs": aa}}
    if st == "div" and pt == "div":
        dn = reconstruct_deriv(source["lhs"], proof["p"])
        dd = reconstruct_deriv(source["rhs"], proof["q"])
        if dn is None or dd is None:
            return None
        num = {
            "tag": "sub",
            "lhs": {"tag": "mul", "lhs": dn, "rhs": source["rhs"]},
            "rhs": {"tag": "mul", "lhs": source["lhs"], "rhs": dd},
        }
        den = {"tag": "mul", "lhs": source["rhs"], "rhs": source["rhs"]}
        return {"tag": "div", "lhs": num, "rhs": den}
    if st == "pow" and pt == "pow":
        if int(source["exp"]) != int(proof["k"]):
            return None
        da = reconstruct_deriv(source["base"], proof["p"])
        if da is None:
            return None
        k = int(source["exp"])
        if k == 0:
            return {"tag": "const", "value": "0"}
        return {
            "tag": "mul",
            "lhs": {
                "tag": "mul",
                "lhs": {"tag": "const", "value": str(k)},
                "rhs": {"tag": "pow", "base": source["base"], "exp": k - 1},
            },
            "rhs": da,
        }
    if st == "sin" and pt == "sin":
        da = reconstruct_deriv(source["arg"], proof["p"])
        if da is None:
            return None
        return {
            "tag": "mul",
            "lhs": {"tag": "cos", "arg": source["arg"]},
            "rhs": da,
        }
    if st == "exp" and pt == "exp":
        da = reconstruct_deriv(source["arg"], proof["p"])
        if da is None:
            return None
        return {
            "tag": "mul",
            "lhs": {"tag": "exp", "arg": source["arg"]},
            "rhs": da,
        }
    if st == "log" and pt == "log":
        da = reconstruct_deriv(source["arg"], proof["p"])
        if da is None:
            return None
        return {"tag": "div", "lhs": da, "rhs": source["arg"]}
    return None


def _expr_eq(a: ExprDict, b: ExprDict) -> bool:
    return a == b


def _obligation_nonzero_ok(obls: list[ObligationDict], oid: int, e: ExprDict) -> bool:
    if oid < 0 or oid >= len(obls):
        return False
    o = obls[oid]
    return o.get("tag") == "nonzero" and _expr_eq(o.get("expr", {}), e)


def _obligation_positive_ok(obls: list[ObligationDict], oid: int, e: ExprDict) -> bool:
    if oid < 0 or oid >= len(obls):
        return False
    o = obls[oid]
    return o.get("tag") == "positive" and _expr_eq(o.get("expr", {}), e)


def check_proof(source: ExprDict, proof: ProofDict, obls: list[ObligationDict]) -> bool:
    pt = str(proof.get("tag", ""))
    st = _tag(source)
    if st == "variable" and int(source["idx"]) == 0 and pt == "variable":
        return True
    if st == "const" and pt == "const":
        return True
    if st == "neg" and pt == "neg":
        return check_proof(source["arg"], proof["p"], obls)
    if st == "add" and pt == "add":
        return check_proof(source["lhs"], proof["p"], obls) and check_proof(
            source["rhs"], proof["q"], obls
        )
    if st == "sub" and pt == "sub":
        return check_proof(source["lhs"], proof["p"], obls) and check_proof(
            source["rhs"], proof["q"], obls
        )
    if st == "mul" and pt == "mul":
        return check_proof(source["lhs"], proof["p"], obls) and check_proof(
            source["rhs"], proof["q"], obls
        )
    if st == "inv" and pt == "inv":
        return _obligation_nonzero_ok(obls, int(proof["obligationId"]), source["arg"]) and check_proof(
            source["arg"], proof["p"], obls
        )
    if st == "div" and pt == "div":
        return (
            _obligation_nonzero_ok(obls, int(proof["obligationId"]), source["rhs"])
            and check_proof(source["lhs"], proof["p"], obls)
            and check_proof(source["rhs"], proof["q"], obls)
        )
    if st == "pow" and pt == "pow":
        return int(source["exp"]) == int(proof["k"]) and check_proof(
            source["base"], proof["p"], obls
        )
    if st == "sin" and pt == "sin":
        return check_proof(source["arg"], proof["p"], obls)
    if st == "exp" and pt == "exp":
        return check_proof(source["arg"], proof["p"], obls)
    if st == "log" and pt == "log":
        return _obligation_positive_ok(obls, int(proof["obligationId"]), source["arg"]) and check_proof(
            source["arg"], proof["p"], obls
        )
    return False


def check_deriv_python(cert: dict[str, Any]) -> bool:
    """Python mirror of Lean `checkDeriv` (syntax / shape only)."""
    if cert.get("claimsCompleteness"):
        return False
    source = cert["source"]
    derivative = cert["derivative"]
    proof = cert["proof"]
    obls = list(cert.get("obligations") or [])
    if expr_size(source) > 10000 or expr_size(derivative) > 10000:
        return False
    if not is_univariate(source) or not is_univariate(derivative):
        return False
    if not check_proof(source, proof, obls):
        return False
    reconstructed = reconstruct_deriv(source, proof)
    return reconstructed is not None and _expr_eq(reconstructed, derivative)


def check_ode_python(cert: dict[str, Any]) -> bool:
    if cert.get("claimsCompleteness"):
        return False
    solution = cert["solution"]
    rhs = cert["rhs"]
    proof = cert["derivProof"]
    obls = list(cert.get("obligations") or [])
    ics = list(cert.get("initialConditions") or [])
    if not is_univariate(solution) or not is_univariate(rhs):
        return False
    if not check_proof(solution, proof, obls):
        return False
    for ic in ics:
        if _tag(ic["point"]) != "const" or _tag(ic["value"]) != "const":
            return False
    reconstructed = reconstruct_deriv(solution, proof)
    return reconstructed is not None and _expr_eq(reconstructed, rhs)


def _build_proof(source: ExprDict, obls: list[ObligationDict]) -> ProofDict:
    """Synthesize a DerivProof tree matching `source` shape."""
    t = _tag(source)
    if t == "variable":
        if int(source["idx"]) != 0:
            raise AnalyticError("multivariate variable")
        return {"tag": "variable"}
    if t == "const":
        return {"tag": "const"}
    if t == "neg":
        return {"tag": "neg", "p": _build_proof(source["arg"], obls)}
    if t == "add":
        return {
            "tag": "add",
            "p": _build_proof(source["lhs"], obls),
            "q": _build_proof(source["rhs"], obls),
        }
    if t == "sub":
        return {
            "tag": "sub",
            "p": _build_proof(source["lhs"], obls),
            "q": _build_proof(source["rhs"], obls),
        }
    if t == "mul":
        return {
            "tag": "mul",
            "p": _build_proof(source["lhs"], obls),
            "q": _build_proof(source["rhs"], obls),
        }
    if t == "inv":
        oid = len(obls)
        obls.append({"tag": "nonzero", "expr": source["arg"]})
        return {"tag": "inv", "p": _build_proof(source["arg"], obls), "obligationId": oid}
    if t == "div":
        oid = len(obls)
        obls.append({"tag": "nonzero", "expr": source["rhs"]})
        return {
            "tag": "div",
            "p": _build_proof(source["lhs"], obls),
            "q": _build_proof(source["rhs"], obls),
            "obligationId": oid,
        }
    if t == "pow":
        return {
            "tag": "pow",
            "k": int(source["exp"]),
            "p": _build_proof(source["base"], obls),
        }
    if t == "sin":
        return {"tag": "sin", "p": _build_proof(source["arg"], obls)}
    if t == "exp":
        return {"tag": "exp", "p": _build_proof(source["arg"], obls)}
    if t == "log":
        oid = len(obls)
        obls.append({"tag": "positive", "expr": source["arg"]})
        return {"tag": "log", "p": _build_proof(source["arg"], obls), "obligationId": oid}
    raise AnalyticError(f"cannot build proof for tag {t!r}")


def propose_deriv_certificate(source: ExprDict) -> dict[str, Any]:
    """Propose a DerivCertificate for `source` (proposal only)."""
    if not is_univariate(source):
        raise AnalyticError("multivariate expressions are unsupported")
    obls: list[ObligationDict] = []
    proof = _build_proof(source, obls)
    derivative = reconstruct_deriv(source, proof)
    if derivative is None:
        raise AnalyticError("failed to reconstruct derivative")
    cert = {
        "schemaVersion": "0.1.0",
        "capability": CAPABILITY_ID,
        "capabilityVersion": CAPABILITY_VERSION,
        "source": source,
        "derivative": derivative,
        "proof": proof,
        "obligations": obls,
        "claimsCompleteness": False,
    }
    if not check_deriv_python(cert):
        raise AnalyticError("proposed certificate failed Python mirror check")
    return cert


def propose_ode_certificate(
    solution: ExprDict,
    *,
    initial_conditions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Propose an ODE certificate for `y' = reconstruct(solution)` with ICs."""
    deriv = propose_deriv_certificate(solution)
    cert = {
        "schemaVersion": "0.1.0",
        "capability": CAPABILITY_ID,
        "capabilityVersion": CAPABILITY_VERSION,
        "solution": solution,
        "rhs": deriv["derivative"],
        "derivProof": deriv["proof"],
        "obligations": deriv["obligations"],
        "initialConditions": list(initial_conditions or []),
        "domain": "univ",
        "claimsCompleteness": False,
    }
    if not check_ode_python(cert):
        raise AnalyticError("proposed ODE certificate failed Python mirror check")
    return cert


@dataclass(frozen=True)
class OfflineFixture:
    name: str
    kind: str
    certificate: dict[str, Any]


OFFLINE_FIXTURES: list[OfflineFixture] = [
    OfflineFixture(
        name="product",
        kind="derivative",
        certificate=propose_deriv_certificate(
            {
                "tag": "mul",
                "lhs": {"tag": "variable", "idx": 0},
                "rhs": {"tag": "variable", "idx": 0},
            }
        ),
    ),
    OfflineFixture(
        name="sin",
        kind="derivative",
        certificate=propose_deriv_certificate({"tag": "sin", "arg": {"tag": "variable", "idx": 0}}),
    ),
    OfflineFixture(
        name="log",
        kind="derivative",
        certificate=propose_deriv_certificate({"tag": "log", "arg": {"tag": "variable", "idx": 0}}),
    ),
    OfflineFixture(
        name="ode_sq",
        kind="ode",
        certificate=propose_ode_certificate(
            {"tag": "pow", "base": {"tag": "variable", "idx": 0}, "exp": 2},
            initial_conditions=[
                {
                    "point": {"tag": "const", "value": "0"},
                    "value": {"tag": "const", "value": "0"},
                }
            ],
        ),
    ),
]
