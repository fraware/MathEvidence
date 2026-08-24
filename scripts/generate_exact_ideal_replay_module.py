#!/usr/bin/env python3
"""Generate an exact ideal-membership Lean replay module.

This generator is untrusted.  The generated module is compiled by Lean and its
resulting declaration is independently inspected from ``Lean.Environment``.
Unlike the historical fixture generator, this module embeds the exact request
claim in the theorem type and the exact request digest/multipliers in the proof.
"""

from __future__ import annotations

import json
import re
from typing import Any

CAPABILITY = "algebra.ideal_membership_witness"


def _safe_ident(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    return cleaned


def _lean_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _as_int(value: Any, *, what: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{what} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{what} must be an integer: {value!r}") from exc


def _validate_poly(poly: dict[str, Any], *, expected: int | None = None) -> int:
    if not isinstance(poly, dict):
        raise ValueError("sparse polynomial must be an object")
    m = _as_int(poly.get("varCount"), what="varCount")
    if m < 0:
        raise ValueError("varCount must be non-negative")
    if expected is not None and m != expected:
        raise ValueError(f"varCount {m} != expected {expected}")
    terms = poly.get("terms")
    if not isinstance(terms, list):
        raise ValueError("sparse polynomial terms must be a list")
    for index, term in enumerate(terms):
        if not isinstance(term, dict):
            raise ValueError(f"term {index} must be an object")
        _as_int(term.get("coefficient"), what=f"term {index} coefficient")
        exponents = term.get("exponents")
        if not isinstance(exponents, list) or len(exponents) != m:
            raise ValueError(f"term {index} exponent arity must equal {m}")
        for e in exponents:
            if _as_int(e, what=f"term {index} exponent") < 0:
                raise ValueError("exponents must be natural numbers")
    return m


def _lean_poly(poly: dict[str, Any], *, m: int) -> str:
    _validate_poly(poly, expected=m)
    terms: list[str] = []
    for term in poly["terms"]:
        coefficient = _as_int(term["coefficient"], what="coefficient")
        exponents = ", ".join(str(_as_int(e, what="exponent")) for e in term["exponents"])
        terms.append(
            "{ coefficient := "
            f"{coefficient}, monomial := Monomial.ofList! {m} [{exponents}] }}"
        )
    return "⟨[" + ", ".join(terms) + "]⟩"


def _lean_poly_array(polys: list[dict[str, Any]], *, m: int) -> str:
    return "#[" + ", ".join(_lean_poly(poly, m=m) for poly in polys) + "]"


def _matching_copy(request: dict[str, Any], certificate: dict[str, Any], field: str) -> None:
    if field in certificate and certificate[field] != request.get(field):
        raise ValueError(f"certificate {field} does not exactly match request {field}")


def generate_exact_ideal_membership_module(
    *,
    module_name: str,
    declaration_name: str,
    request: dict[str, Any],
    certificate: dict[str, Any],
    candidate_bundle_digest: str,
) -> str:
    if request.get("capability") != CAPABILITY:
        raise ValueError("exact ideal replay received a different capability")
    if certificate.get("capability", CAPABILITY) != CAPABILITY:
        raise ValueError("certificate capability does not match request")

    request_digest = request.get("requestDigest")
    if not isinstance(request_digest, str) or not request_digest.startswith("sha256:"):
        raise ValueError("requestDigest missing or invalid")
    if certificate.get("requestDigest") != request_digest:
        raise ValueError("certificate requestDigest does not match request")

    requested_claim = request.get("requestedClaim")
    if requested_claim not in {"witness", "soundResult"}:
        raise ValueError(
            "theorem-producing ideal replay requires requestedClaim witness or soundResult"
        )
    if certificate.get("claimClass") not in {None, requested_claim}:
        raise ValueError("certificate claimClass does not match requestedClaim")

    _matching_copy(request, certificate, "target")
    _matching_copy(request, certificate, "generators")

    target = request.get("target")
    generators = request.get("generators")
    multipliers = certificate.get("multipliers")
    if not isinstance(target, dict):
        raise ValueError("request target must be a sparse polynomial")
    if not isinstance(generators, list) or not generators:
        raise ValueError("request generators must be a non-empty list")
    if not all(isinstance(poly, dict) for poly in generators):
        raise ValueError("request generators must be sparse polynomial objects")
    if not isinstance(multipliers, list) or not all(
        isinstance(poly, dict) for poly in multipliers
    ):
        raise ValueError("certificate multipliers must be sparse polynomial objects")
    if len(generators) != len(multipliers):
        raise ValueError("multiplier count must equal generator count")

    m = _validate_poly(target)
    target_lean = _lean_poly(target, m=m)
    generators_lean = _lean_poly_array(generators, m=m)
    multipliers_lean = _lean_poly_array(multipliers, m=m)
    claim_class = ".witness" if requested_claim == "witness" else ".soundResult"
    claim_expr = (
        f"({{ target := {target_lean}, generators := {generators_lean}, "
        f"claimClass := {claim_class} }} : Claim {m})"
    )
    decl = _safe_ident(declaration_name)

    return f"""/-
AUTO-GENERATED — UNTRUSTED exact-candidate replay source.
moduleName = {module_name}
candidateBundleDigest = {candidate_bundle_digest}
requestDigest = {request_digest}
-/
import MathEvidence.Checkers.IdealMembership.ReplaySound

open MathEvidence.Core
open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership

/-- Exact Candidate Bundle semantic claim. -/
theorem {decl} : Claim.proposition {claim_expr} := by
  let req : Request {m} := {{
    claim := {claim_expr}
    requestDigest := ⟨{_lean_string(request_digest)}⟩
  }}
  let cert : Certificate {m} := {{
    requestDigest := ⟨{_lean_string(request_digest)}⟩
    multipliers := {multipliers_lean}
  }}
  exact replaySound req cert
    (by native_decide : checkBool req cert = true)

#print axioms {decl}
"""
