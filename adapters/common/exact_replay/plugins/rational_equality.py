"""Exact rational-equality plugin."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adapters.common.exact_replay.lean_syntax import (
    lean_expr_list,
    lean_rational_expr,
    lean_string,
    lean_string_list,
    matching_copy,
    reject_float_payload,
    safe_ident,
    validate_digest,
    validate_rational_expr,
    validate_schema_version,
    validate_semver,
)
from adapters.common.exact_replay.pipeline import CanonicalCandidate, ReplayIR
from adapters.common.exact_replay.registry import register_plugin
from adapters.common.limits import ResourceLimits

CAPABILITY = "algebra.rational_equality"
CAPABILITY_VERSION = "0.1.0"
GENERATOR_ID = "mathevidence.exact_rational_equality"
GENERATOR_VERSION = "0.1.0"
GRAMMAR_VERSION = "0.1.0"
VERIFIER = "mathevidence-declaration-identity"
# ``MathEvidence.Checkers.RationalEquality.Wire.claimToRequestJson`` currently
# reconstructs exactly this v0.1 policy. Exact theorem replay must reject any
# broader wire policy until the Lean binding projection carries those fields.
EXACT_RESOURCE_POLICY = {
    "maxWallTimeMs": 10000,
    "maxOutputBytes": 1048576,
}


def _validate_exact_expr(
    value: Any,
    *,
    var_names: list[str],
    what: str,
) -> dict[str, Any]:
    """Validate an expression without silently changing request wire semantics.

    ``validate_rational_expr`` canonicalizes rational literals (for example
    ``2/4`` to ``1/2``). That normalization is useful for non-theorem adapter
    handling, but exact candidate replay must reconstruct the same wire object
    whose digest the submitter bound. The Lean v0.1 wire projection emits
    canonical integer/rational syntax, so non-canonical inputs are unsupported
    here and fail closed rather than being normalized behind the digest.
    """
    canonical = validate_rational_expr(value, var_names=var_names, what=what)
    if canonical != value:
        raise ValueError(
            f"{what} must use canonical exact RationalExpr wire syntax; "
            "silent normalization is not permitted for exact candidate binding"
        )
    return canonical


@dataclass(frozen=True)
class RationalEqualityPlugin:
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
        del limits
        reject_float_payload(request, path="request")
        reject_float_payload(certificate, path="certificate")
        validate_schema_version(request.get("schemaVersion"))
        validate_schema_version(certificate.get("schemaVersion"))
        if request.get("capability") != CAPABILITY:
            raise ValueError("exact rational replay received a different capability")
        if certificate.get("capability") != CAPABILITY:
            raise ValueError("certificate capability does not match request")

        matching_copy(request, certificate, "schemaVersion")
        matching_copy(request, certificate, "capabilityVersion")
        capability_version = validate_semver(
            request.get("capabilityVersion"), what="request capabilityVersion"
        )
        if capability_version != CAPABILITY_VERSION:
            raise ValueError(
                f"exact rational replay supports capabilityVersion {CAPABILITY_VERSION} only; "
                "the Lean v0.1 wire binding must be extended before another version is eligible"
            )
        if certificate.get("capabilityVersion") != capability_version:
            raise ValueError("certificate capabilityVersion does not match request")

        resource_policy = request.get("resourcePolicy")
        if resource_policy != EXACT_RESOURCE_POLICY:
            raise ValueError(
                "exact rational replay requires resourcePolicy "
                f"{EXACT_RESOURCE_POLICY!r}; broader policy fields are not yet represented "
                "by the Lean v0.1 request-binding projection"
            )

        request_digest = validate_digest(request.get("requestDigest"), what="requestDigest")
        validate_digest(candidate_bundle_digest, what="candidateBundleDigest")
        if certificate.get("requestDigest") != request_digest:
            raise ValueError("certificate requestDigest does not match request")

        if request.get("requestedClaim") != "soundResult":
            raise ValueError("theorem-producing rational replay requires soundResult")

        variables = request.get("variables")
        if not isinstance(variables, list):
            raise ValueError("request variables must be a list")
        var_names: list[str] = []
        for index, var in enumerate(variables):
            if not isinstance(var, dict):
                raise ValueError(f"variable {index} must be an object")
            name = var.get("name")
            if not isinstance(name, str) or not name:
                raise ValueError(f"variable {index} name invalid")
            if var.get("type") != "Rat":
                raise ValueError(f"variable {index} type must be Rat")
            if set(var) != {"name", "type"}:
                raise ValueError(
                    f"variable {index} contains fields outside the Lean v0.1 wire projection"
                )
            if name in var_names:
                raise ValueError(f"duplicate variable name {name!r}")
            var_names.append(name)

        lhs = _validate_exact_expr(request.get("lhs"), var_names=var_names, what="lhs")
        rhs = _validate_exact_expr(request.get("rhs"), var_names=var_names, what="rhs")

        assumptions_raw = request.get("knownAssumptions")
        if not isinstance(assumptions_raw, list):
            raise ValueError("knownAssumptions must be a list")
        assumptions: list[dict[str, Any]] = []
        for index, item in enumerate(assumptions_raw):
            if not isinstance(item, dict) or item.get("kind") != "nonzero":
                raise ValueError(f"knownAssumptions[{index}] must be kind=nonzero")
            if set(item) != {"kind", "expr"}:
                raise ValueError(
                    f"knownAssumptions[{index}] contains fields outside the Lean v0.1 wire projection"
                )
            assumptions.append(
                _validate_exact_expr(
                    item.get("expr"),
                    var_names=var_names,
                    what=f"knownAssumptions[{index}].expr",
                )
            )

        factors_raw = certificate.get("denominatorFactors")
        if not isinstance(factors_raw, list):
            raise ValueError("certificate denominatorFactors must be a list")
        denom_factors: list[dict[str, Any]] = []
        for index, item in enumerate(factors_raw):
            if not isinstance(item, dict):
                raise ValueError(f"denominatorFactors[{index}] must be an object")
            role = item.get("role")
            if role not in {"original_division", "common_denominator", "factorization"}:
                raise ValueError(f"denominatorFactors[{index}] role unsupported")
            canonical_expr = _validate_exact_expr(
                item.get("expr"),
                var_names=var_names,
                what=f"denominatorFactors[{index}].expr",
            )
            denom_factors.append(canonical_expr)

        # differenceNumerator is diagnostic; reject malformed/non-canonical when present so
        # the generated source never silently rewrites an exact Candidate Bundle field.
        if "differenceNumerator" in certificate:
            _validate_exact_expr(
                certificate["differenceNumerator"],
                var_names=var_names,
                what="differenceNumerator",
            )

        return CanonicalCandidate(
            capability_id=CAPABILITY,
            capability_version=capability_version,
            request={
                **request,
                "lhs": lhs,
                "rhs": rhs,
                "knownAssumptions": [{"kind": "nonzero", "expr": e} for e in assumptions],
            },
            certificate={
                **certificate,
                "denominatorFactors": [
                    {"expr": e, "role": factors_raw[i].get("role", "original_division")}
                    for i, e in enumerate(denom_factors)
                ],
            },
            candidate_bundle_digest=candidate_bundle_digest,
            request_digest=request_digest,
            claim_class="soundResult",
            extras={
                "var_names": var_names,
                "lhs": lhs,
                "rhs": rhs,
                "assumptions": assumptions,
                "denom_factors": denom_factors,
            },
        )

    def to_replay_ir(
        self,
        canonical: CanonicalCandidate,
        *,
        module_name: str,
        declaration_name: str,
    ) -> ReplayIR:
        return ReplayIR(
            capability_id=CAPABILITY,
            generator_id=self.generator_id,
            generator_version=self.generator_version,
            grammar_version=self.grammar_version,
            module_name=module_name,
            declaration_name=safe_ident(declaration_name),
            nodes=(
                ("var_names", tuple(canonical.extras["var_names"])),
                ("lhs", canonical.extras["lhs"]),
                ("rhs", canonical.extras["rhs"]),
                ("assumptions", tuple(canonical.extras["assumptions"])),
                ("denom_factors", tuple(canonical.extras["denom_factors"])),
                ("request_digest", canonical.request_digest),
                ("candidate_bundle_digest", canonical.candidate_bundle_digest),
                ("capability_version", canonical.capability_version),
            ),
            metadata={
                "request_digest": canonical.request_digest,
                "candidate_bundle_digest": canonical.candidate_bundle_digest,
            },
        )

    def render(self, ir: ReplayIR) -> str:
        meta = {node[0]: node[1] for node in ir.nodes}
        var_names = list(meta["var_names"])
        lhs = lean_rational_expr(meta["lhs"], var_names)
        rhs = lean_rational_expr(meta["rhs"], var_names)
        assumptions = lean_expr_list(list(meta["assumptions"]), var_names)
        denoms = lean_expr_list(list(meta["denom_factors"]), var_names)
        names = lean_string_list(var_names)
        request_digest = meta["request_digest"]
        candidate_bundle_digest = meta["candidate_bundle_digest"]
        decl = ir.declaration_name

        claim_fields = (
            f"  varNames := {names}\n"
            f"  lhs := {lhs}\n"
            f"  rhs := {rhs}\n"
            f"  knownAssumptions := {assumptions}\n"
            f"  claimClass := .soundResult"
        )
        claim_name = f"{decl}_claim"
        req_name = f"{decl}_req"
        cert_name = f"{decl}_cert"
        binding_decl = f"{decl}_request_binding"

        return f"""/-
AUTO-GENERATED -- UNTRUSTED exact-candidate replay source.
moduleName = {ir.module_name}
candidateBundleDigest = {candidate_bundle_digest}
requestDigest = {request_digest}
generatorId = {ir.generator_id}
generatorVersion = {ir.generator_version}
grammarVersion = {ir.grammar_version}
-/
import MathEvidence.Checkers.RationalEquality.ReplaySound
import MathEvidence.Checkers.RationalEquality.Wire

open MathEvidence.Core
open MathEvidence.IR.RationalExpr
open MathEvidence.Checkers.RationalEquality

def {claim_name} : Claim where
{claim_fields}

/-- Reconstruct the request digest from Lean wire semantics; callers do not supply it. -/
def {req_name} : Request :=
  Request.ofClaim! {claim_name}

def {cert_name} : Certificate where
  requestDigest := ⟨{lean_string(request_digest)}⟩
  denomFactors := {denoms}

/-- Lean-side equality between reconstructed wire binding and submitted digest.
The submitted digest is not copied into the request: `native_decide` evaluates
Lean's canonical-JSON/SHA-256 reconstruction of `Request.ofClaim!`. -/
theorem {binding_decl} :
    {req_name}.requestDigest = ⟨{lean_string(request_digest)}⟩ := by
  native_decide

/-- Exact Candidate Bundle semantic claim. The checker includes digest equality,
so this native decision independently re-evaluates the same request binding. -/
theorem {decl} : Claim.proposition {req_name}.claim {cert_name}.denomFactors :=
  replaySound
    {req_name}
    {cert_name}
    (by native_decide : checkBool {req_name} {cert_name} = true)

#print axioms {binding_decl}
#print axioms {decl}
"""


PLUGIN = RationalEqualityPlugin()
register_plugin(PLUGIN)


def generate_exact_rational_equality_module(
    *,
    module_name: str,
    declaration_name: str,
    request: dict[str, Any],
    certificate: dict[str, Any],
    candidate_bundle_digest: str,
) -> str:
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
