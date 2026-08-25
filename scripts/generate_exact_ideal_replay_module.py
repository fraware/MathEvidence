#!/usr/bin/env python3
"""Generate an exact ideal-membership Lean replay module.

This generator is untrusted. The generated module reconstructs the exact
mathematical claim and witness, but request identity is recomputed inside Lean
from the reconstructed wire-semantic fields before the checker can establish a
theorem.  The historical fixture generator is not used by this path.
"""

from __future__ import annotations

import json
import re
from typing import Any

CAPABILITY = "algebra.ideal_membership_witness"
_SCHEMA_VERSION = "0.1.0"
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _safe_ident(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    return cleaned


def _lean_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _lean_string_list(values: list[str]) -> str:
    return "[" + ", ".join(_lean_string(value) for value in values) + "]"


def _as_int(value: Any, *, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be an integer: {value!r}")
    return value


def _validate_digest(value: Any, *, what: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{what} must be a canonical sha256 digest")
    return value


def _validate_semver(value: Any, *, what: str) -> str:
    if not isinstance(value, str) or _SEMVER_RE.fullmatch(value) is None:
        raise ValueError(f"{what} must be a semantic version")
    return value


def _validate_schema_version(value: Any, *, what: str) -> str:
    if value != _SCHEMA_VERSION:
        raise ValueError(f"{what} must be {_SCHEMA_VERSION}")
    return _SCHEMA_VERSION


def _validate_notes(value: Any) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("request notes must be an array of strings")
    if any(len(item) > 2048 for item in value):
        raise ValueError("request note exceeds 2048 characters")
    return list(value)


def _validate_poly(poly: dict[str, Any], *, expected: int | None = None) -> int:
    if not isinstance(poly, dict):
        raise ValueError("sparse polynomial must be an object")
    m = _as_int(poly.get("varCount"), what="varCount")
    if m < 0 or m > 256:
        raise ValueError("varCount must be between 0 and 256")
    if expected is not None and m != expected:
        raise ValueError(f"varCount {m} != expected {expected}")
    terms = poly.get("terms")
    if not isinstance(terms, list):
        raise ValueError("sparse polynomial terms must be a list")
    if len(terms) > 4096:
        raise ValueError("sparse polynomial exceeds 4096 terms")
    for index, term in enumerate(terms):
        if not isinstance(term, dict):
            raise ValueError(f"term {index} must be an object")
        _as_int(term.get("coefficient"), what=f"term {index} coefficient")
        exponents = term.get("exponents")
        if not isinstance(exponents, list) or len(exponents) != m:
            raise ValueError(f"term {index} exponent arity must equal {m}")
        for exponent in exponents:
            if _as_int(exponent, what=f"term {index} exponent") < 0:
                raise ValueError("exponents must be natural numbers")
    return m


def _lean_poly(poly: dict[str, Any], *, m: int) -> str:
    _validate_poly(poly, expected=m)
    terms: list[str] = []
    for term in poly["terms"]:
        coefficient = _as_int(term["coefficient"], what="coefficient")
        exponents = ", ".join(
            str(_as_int(exponent, what="exponent")) for exponent in term["exponents"]
        )
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
    _validate_schema_version(request.get("schemaVersion"), what="request schemaVersion")
    _validate_schema_version(certificate.get("schemaVersion"), what="certificate schemaVersion")
    if request.get("capability") != CAPABILITY:
        raise ValueError("exact ideal replay received a different capability")
    if certificate.get("capability") != CAPABILITY:
        raise ValueError("certificate capability does not match request")

    _matching_copy(request, certificate, "schemaVersion")
    _matching_copy(request, certificate, "capabilityVersion")
    capability_version = _validate_semver(
        request.get("capabilityVersion"), what="request capabilityVersion"
    )
    if certificate.get("capabilityVersion") != capability_version:
        raise ValueError("certificate capabilityVersion does not match request")

    request_digest = _validate_digest(request.get("requestDigest"), what="requestDigest")
    _validate_digest(candidate_bundle_digest, what="candidateBundleDigest")
    if certificate.get("requestDigest") != request_digest:
        raise ValueError("certificate requestDigest does not match request")

    requested_claim = request.get("requestedClaim")
    if requested_claim not in {"witness", "soundResult"}:
        raise ValueError(
            "theorem-producing ideal replay requires requestedClaim witness or soundResult"
        )
    if certificate.get("claimClass") != requested_claim:
        raise ValueError("certificate claimClass does not match requestedClaim")

    notes = _validate_notes(request.get("notes"))
    notes_expr = "none" if notes is None else f"some {_lean_string_list(notes)}"

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
    capability_expr = (
        f"({{ id := {_lean_string(CAPABILITY)}, version := {_lean_string(capability_version)} }} "
        ": CapabilityRef)"
    )
    claim_expr = (
        f"({{ target := {target_lean}, generators := {generators_lean}, "
        f"claimClass := {claim_class} }} : Claim {m})"
    )
    req_expr = f"Request.ofWireFields! {capability_expr} {claim_expr} {notes_expr}"
    decl = _safe_ident(declaration_name)
    binding_decl = f"{decl}_request_binding"

    return f"""/-
AUTO-GENERATED — UNTRUSTED exact-candidate replay source.
moduleName = {module_name}
candidateBundleDigest = {candidate_bundle_digest}
requestDigest = {request_digest}
-/
import MathEvidence.Checkers.IdealMembership.ReplaySound
import MathEvidence.Checkers.IdealMembership.Wire

open MathEvidence.Core
open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership

/-- Lean-side request binding for the reconstructed exact wire semantics. -/
theorem {binding_decl} :
    ({req_expr}).requestDigest = ⟨{_lean_string(request_digest)}⟩ := by
  native_decide

/-- Exact Candidate Bundle semantic claim. -/
theorem {decl} : Claim.proposition {claim_expr} := by
  let req : Request {m} := {req_expr}
  let cert : Certificate {m} := {{
    requestDigest := ⟨{_lean_string(request_digest)}⟩
    multipliers := {multipliers_lean}
  }}
  have hCheck : checkBool req cert = true := by
    native_decide
  exact replaySound req cert hCheck

#print axioms {binding_decl}
#print axioms {decl}
"""
