"""Exact ideal-membership plugin (SPEC-03 migration of PR #53 generator).

Mathematical obligation is unchanged: inline exact request/certificate wire
semantics, ``replaySound``, and declaration-identity readback. No OfflineFixtures.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from adapters.common.exact_replay.pipeline import CanonicalCandidate, ReplayIR
from adapters.common.exact_replay.registry import register_plugin
from adapters.common.limits import ResourceLimits
from adapters.common.security_bounds import enforce_integer_digits

CAPABILITY = "algebra.ideal_membership_witness"
GENERATOR_ID = "mathevidence.exact_ideal_membership"
GENERATOR_VERSION = "0.1.0"
GRAMMAR_VERSION = "0.1.0"
VERIFIER = "mathevidence-declaration-identity"
_SCHEMA_VERSION = "0.1.0"
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_MAX_VAR_COUNT = 256
_MAX_TERMS = 4096
_MAX_INTEGER_DIGITS = 4096


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
    enforce_integer_digits(str(value), max_digits=_MAX_INTEGER_DIGITS)
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
    if m < 0 or m > _MAX_VAR_COUNT:
        raise ValueError(f"varCount must be between 0 and {_MAX_VAR_COUNT}")
    if expected is not None and m != expected:
        raise ValueError(f"varCount {m} != expected {expected}")
    terms = poly.get("terms")
    if not isinstance(terms, list):
        raise ValueError("sparse polynomial terms must be a list")
    if len(terms) > _MAX_TERMS:
        raise ValueError(f"sparse polynomial exceeds {_MAX_TERMS} terms")
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
    if not poly["terms"]:
        # Match OfflineFixtures / SparsePoly.zero — empty ⟨[]⟩ is not a closed SparsePoly.
        return f"(SparsePoly.zero {m})"
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


@dataclass(frozen=True)
class _IdealPolyNode:
    kind: str  # target | generators | multipliers
    var_count: int
    payload: Any


@dataclass(frozen=True)
class IdealMembershipPlugin:
    capability_id: str = CAPABILITY
    generator_id: str = GENERATOR_ID
    generator_version: str = GENERATOR_VERSION
    grammar_version: str = GRAMMAR_VERSION
    verifier: str = VERIFIER

    def parse_and_validate(
        self,
        *,
        request: dict[str, Any],
        certificate: dict[str, Any],
        candidate_bundle_digest: str,
        limits: ResourceLimits,
    ) -> CanonicalCandidate:
        del limits  # nesting already enforced by pipeline; poly limits local
        _validate_schema_version(request.get("schemaVersion"), what="request schemaVersion")
        _validate_schema_version(
            certificate.get("schemaVersion"), what="certificate schemaVersion"
        )
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
        for poly in generators:
            _validate_poly(poly, expected=m)
        for poly in multipliers:
            _validate_poly(poly, expected=m)

        return CanonicalCandidate(
            capability_id=CAPABILITY,
            capability_version=capability_version,
            request=dict(request),
            certificate=dict(certificate),
            candidate_bundle_digest=candidate_bundle_digest,
            request_digest=request_digest,
            claim_class=str(requested_claim),
            extras={"notes": notes, "var_count": m},
        )

    def to_replay_ir(
        self,
        canonical: CanonicalCandidate,
        *,
        module_name: str,
        declaration_name: str,
    ) -> ReplayIR:
        request = canonical.request
        certificate = canonical.certificate
        m = int(canonical.extras["var_count"])
        nodes = (
            _IdealPolyNode("target", m, request["target"]),
            _IdealPolyNode("generators", m, request["generators"]),
            _IdealPolyNode("multipliers", m, certificate["multipliers"]),
            ("claim_class", canonical.claim_class),
            ("notes", canonical.extras.get("notes")),
            ("capability_version", canonical.capability_version),
            ("request_digest", canonical.request_digest),
            ("candidate_bundle_digest", canonical.candidate_bundle_digest),
        )
        return ReplayIR(
            capability_id=CAPABILITY,
            generator_id=self.generator_id,
            generator_version=self.generator_version,
            grammar_version=self.grammar_version,
            module_name=module_name,
            declaration_name=_safe_ident(declaration_name),
            nodes=nodes,
            metadata={
                "request_digest": canonical.request_digest,
                "candidate_bundle_digest": canonical.candidate_bundle_digest,
                "var_count": m,
            },
        )

    def render(self, ir: ReplayIR) -> str:
        by_kind = {node.kind: node for node in ir.nodes if isinstance(node, _IdealPolyNode)}
        meta = {node[0]: node[1] for node in ir.nodes if isinstance(node, tuple)}
        m = by_kind["target"].var_count
        target_lean = _lean_poly(by_kind["target"].payload, m=m)
        generators_lean = _lean_poly_array(by_kind["generators"].payload, m=m)
        multipliers_lean = _lean_poly_array(by_kind["multipliers"].payload, m=m)
        requested_claim = meta["claim_class"]
        claim_class = ".witness" if requested_claim == "witness" else ".soundResult"
        notes = meta["notes"]
        notes_expr = "none" if notes is None else f"some {_lean_string_list(notes)}"
        capability_version = meta["capability_version"]
        request_digest = meta["request_digest"]
        candidate_bundle_digest = meta["candidate_bundle_digest"]
        capability_expr = (
            f"({{ id := {_lean_string(CAPABILITY)}, version := {_lean_string(capability_version)} }} "
            ": CapabilityRef)"
        )
        decl = ir.declaration_name
        claim_name = f"{decl}_claim"
        req_name = f"{decl}_req"
        cert_name = f"{decl}_cert"
        binding_decl = f"{decl}_request_binding"
        module_name = ir.module_name

        # Named defs mirror OfflineFixtures: theorem type must be
        # ``Claim.proposition req.claim`` so ``replaySound`` unifies. Inlining a
        # second copy of the claim literal breaks definitional equality and
        # leaves ``sorryAx`` on the failed exact.
        return f"""/-
AUTO-GENERATED -- UNTRUSTED exact-candidate replay source.
moduleName = {module_name}
candidateBundleDigest = {candidate_bundle_digest}
requestDigest = {request_digest}
generatorId = {ir.generator_id}
generatorVersion = {ir.generator_version}
grammarVersion = {ir.grammar_version}
-/
import MathEvidence.Checkers.IdealMembership.ReplaySound
import MathEvidence.Checkers.IdealMembership.Wire

open MathEvidence.Core
open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership

def {claim_name} : Claim {m} where
  target := {target_lean}
  generators := {generators_lean}
  claimClass := {claim_class}

def {req_name} : Request {m} :=
  Request.ofWireFields! {capability_expr} {claim_name} {notes_expr}

def {cert_name} : Certificate {m} where
  requestDigest := ⟨{_lean_string(request_digest)}⟩
  multipliers := {multipliers_lean}

/-- Lean-side request binding for the reconstructed exact wire semantics. -/
theorem {binding_decl} :
    {req_name}.requestDigest = ⟨{_lean_string(request_digest)}⟩ := by
  native_decide

/-- Exact Candidate Bundle semantic claim. -/
theorem {decl} : Claim.proposition {req_name}.claim :=
  replaySound
    {req_name}
    {cert_name}
    (by native_decide : checkBool {req_name} {cert_name} = true)

#print axioms {binding_decl}
#print axioms {decl}
"""


PLUGIN = IdealMembershipPlugin()
register_plugin(PLUGIN)


def generate_exact_ideal_membership_module(
    *,
    module_name: str,
    declaration_name: str,
    request: dict[str, Any],
    certificate: dict[str, Any],
    candidate_bundle_digest: str,
) -> str:
    """Backward-compatible entry point used by scripts and existing tests."""
    from adapters.common.exact_replay.pipeline import generate_module

    module = generate_module(
        capability_id=CAPABILITY,
        request=request,
        certificate=certificate,
        candidate_bundle_digest=candidate_bundle_digest,
        module_name=module_name,
        declaration_name=declaration_name,
    )
    return module.source_text
