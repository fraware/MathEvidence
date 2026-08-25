"""Exact formal rational calculus plugin (SPEC-07 Track A)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adapters.common.exact_replay.lean_syntax import (
    lean_expr_list,
    lean_nat,
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

CAPABILITY = "algebra.formal_rational_calculus"
GENERATOR_ID = "mathevidence.exact_formal_rational_calculus"
GENERATOR_VERSION = "0.1.0"
GRAMMAR_VERSION = "0.1.0"
VERIFIER = "mathevidence-declaration-identity"

OPERATIONS = frozenset(
    {
        "derivative_candidate",
        "antiderivative_candidate",
        "recurrence_identity",
        "ode_candidate",
    }
)
_OP_LEAN = {
    "derivative_candidate": ".derivativeCandidate",
    "antiderivative_candidate": ".antiderivativeCandidate",
    "recurrence_identity": ".recurrenceIdentity",
    "ode_candidate": ".odeCandidate",
}


@dataclass(frozen=True)
class FormalRationalCalculusPlugin:
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
            raise ValueError("exact formal calculus replay received a different capability")
        if certificate.get("capability") != CAPABILITY:
            raise ValueError("certificate capability does not match request")

        matching_copy(request, certificate, "schemaVersion")
        matching_copy(request, certificate, "capabilityVersion")
        capability_version = validate_semver(
            request.get("capabilityVersion"), what="request capabilityVersion"
        )
        if certificate.get("capabilityVersion") != capability_version:
            raise ValueError("certificate capabilityVersion does not match request")

        request_digest = validate_digest(request.get("requestDigest"), what="requestDigest")
        validate_digest(candidate_bundle_digest, what="candidateBundleDigest")
        if certificate.get("requestDigest") != request_digest:
            raise ValueError("certificate requestDigest does not match request")

        operation = request.get("operation")
        if operation not in OPERATIONS:
            raise ValueError(f"unsupported formal calculus operation: {operation!r}")
        if certificate.get("operation") != operation:
            raise ValueError("certificate operation does not match request")

        requested = request.get("requestedClaim")
        if requested not in {"soundResult", "witness", "candidate"}:
            raise ValueError(f"unsupported requestedClaim {requested!r}")
        # Theorem path uses soundResult/witness; candidate remains evidence-only.
        if requested == "candidate":
            raise ValueError("candidate claim cannot mint formal calculus theorems")
        claim_class = "soundResult" if requested == "soundResult" else "witness"

        variables = request.get("variables")
        if not isinstance(variables, list) or not variables:
            raise ValueError("variables must be a nonempty list")
        var_names: list[str] = []
        for index, var in enumerate(variables):
            if not isinstance(var, dict):
                raise ValueError(f"variables[{index}] must be an object")
            name = var.get("name")
            if not isinstance(name, str) or not name:
                raise ValueError(f"variables[{index}] name invalid")
            if name in var_names:
                raise ValueError(f"duplicate variable {name!r}")
            var_names.append(name)

        independent = request.get("independentVar")
        if independent not in var_names:
            raise ValueError("independentVar must be one of the variables")
        independent_idx = var_names.index(independent)
        dependent = request.get("dependentVar")
        # Default dependent to independent (univariate derivative/antiderivative).
        # Recurrence/ODE must supply an explicit in-range dependentVar.
        if dependent is None:
            dependent_idx = independent_idx
        else:
            if dependent not in var_names:
                raise ValueError("dependentVar must be one of the variables")
            dependent_idx = var_names.index(dependent)

        expr = validate_rational_expr(request.get("expr"), var_names=var_names, what="expr")
        candidate_expr = request.get("candidate")
        if candidate_expr is None:
            candidate_expr = {"tag": "int", "value": "0"}
        candidate = validate_rational_expr(
            candidate_expr, var_names=var_names, what="candidate"
        )

        domain_raw = request.get("domainConditions")
        if not isinstance(domain_raw, list):
            raise ValueError("domainConditions must be a list")
        domain_conditions = [
            validate_rational_expr(item, var_names=var_names, what=f"domainConditions[{i}]")
            for i, item in enumerate(domain_raw)
        ]
        cert_domain = certificate.get("domainConditions", domain_raw)
        if not isinstance(cert_domain, list):
            raise ValueError("certificate domainConditions must be a list")
        cert_domain_conditions = [
            validate_rational_expr(
                item, var_names=var_names, what=f"certificate.domainConditions[{i}]"
            )
            for i, item in enumerate(cert_domain)
        ]
        if cert_domain_conditions != domain_conditions:
            raise ValueError("certificate domainConditions must match request")

        ode_rhs = None
        recurrence_rhs = None
        initial_conditions: list[dict[str, Any]] = []
        if operation == "ode_candidate":
            ode_rhs = validate_rational_expr(
                request.get("odeRhs"), var_names=var_names, what="odeRhs"
            )
            ics = request.get("initialConditions") or []
            if not isinstance(ics, list):
                raise ValueError("initialConditions must be a list")
            for i, ic in enumerate(ics):
                if not isinstance(ic, dict):
                    raise ValueError(f"initialConditions[{i}] must be an object")
                initial_conditions.append(
                    {
                        "point": validate_rational_expr(
                            ic.get("point"), var_names=var_names, what=f"ic[{i}].point"
                        ),
                        "value": validate_rational_expr(
                            ic.get("value"), var_names=var_names, what=f"ic[{i}].value"
                        ),
                    }
                )
        if operation == "recurrence_identity":
            recurrence_rhs = validate_rational_expr(
                request.get("recurrenceRhs"), var_names=var_names, what="recurrenceRhs"
            )

        return CanonicalCandidate(
            capability_id=CAPABILITY,
            capability_version=capability_version,
            request=dict(request),
            certificate=dict(certificate),
            candidate_bundle_digest=candidate_bundle_digest,
            request_digest=request_digest,
            claim_class=claim_class,
            extras={
                "operation": operation,
                "var_names": var_names,
                "independent_idx": independent_idx,
                "dependent_idx": dependent_idx,
                "expr": expr,
                "candidate": candidate,
                "domain_conditions": domain_conditions,
                "ode_rhs": ode_rhs,
                "recurrence_rhs": recurrence_rhs,
                "initial_conditions": initial_conditions,
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
            nodes=tuple(canonical.extras.items())
            + (
                ("request_digest", canonical.request_digest),
                ("candidate_bundle_digest", canonical.candidate_bundle_digest),
                ("claim_class", canonical.claim_class),
            ),
            metadata={
                "request_digest": canonical.request_digest,
                "candidate_bundle_digest": canonical.candidate_bundle_digest,
                "operation": canonical.extras["operation"],
            },
        )

    def render(self, ir: ReplayIR) -> str:
        meta = {node[0]: node[1] for node in ir.nodes}
        var_names = list(meta["var_names"])
        names = lean_string_list(var_names)
        op = meta["operation"]
        expr = lean_rational_expr(meta["expr"], var_names)
        candidate = lean_rational_expr(meta["candidate"], var_names)
        domains = lean_expr_list(list(meta["domain_conditions"]), var_names)
        ics = meta["initial_conditions"]
        if ics:
            ic_parts = []
            for ic in ics:
                pt = lean_rational_expr(ic["point"], var_names)
                val = lean_rational_expr(ic["value"], var_names)
                ic_parts.append(f"{{ point := {pt}, value := {val} }}")
            ics_lean = "[" + ", ".join(ic_parts) + "]"
        else:
            ics_lean = "[]"
        ode = (
            f"some ({lean_rational_expr(meta['ode_rhs'], var_names)})"
            if meta["ode_rhs"] is not None
            else "none"
        )
        rec = (
            f"some ({lean_rational_expr(meta['recurrence_rhs'], var_names)})"
            if meta["recurrence_rhs"] is not None
            else "none"
        )
        claim_class = ".soundResult" if meta["claim_class"] == "soundResult" else ".witness"
        request_digest = meta["request_digest"]
        candidate_bundle_digest = meta["candidate_bundle_digest"]
        decl = ir.declaration_name
        claim_name = f"{decl}_claim"
        req_name = f"{decl}_req"
        cert_name = f"{decl}_cert"
        binding_decl = f"{decl}_request_binding"
        claim_fields = (
            f"  operation := {_OP_LEAN[op]}\n"
            f"  varNames := {names}\n"
            f"  independentVar := {lean_nat(int(meta['independent_idx']))}\n"
            f"  dependentVar := {lean_nat(int(meta['dependent_idx']))}\n"
            f"  expr := {expr}\n"
            f"  candidate := {candidate}\n"
            f"  domainConditions := {domains}\n"
            f"  initialConditions := {ics_lean}\n"
            f"  odeRhs := {ode}\n"
            f"  recurrenceRhs := {rec}\n"
            f"  claimClass := {claim_class}"
        )
        return f"""/-
AUTO-GENERATED -- UNTRUSTED exact-candidate replay source.
moduleName = {ir.module_name}
candidateBundleDigest = {candidate_bundle_digest}
requestDigest = {request_digest}
generatorId = {ir.generator_id}
generatorVersion = {ir.generator_version}
grammarVersion = {ir.grammar_version}
operation = {op}
scope = formal_rational_calculus_not_analytic
-/
import MathEvidence.Checkers.Calculus.ReplaySound
import MathEvidence.IR.CalculusExpr.Syntax
import MathEvidence.IR.RationalExpr.Syntax

open MathEvidence.Core
open MathEvidence.IR.CalculusExpr
open MathEvidence.IR.RationalExpr (Expr)
open MathEvidence.Checkers.Calculus

def {claim_name} : Claim where
{claim_fields}

def {req_name} : Request where
  claim := {claim_name}
  requestDigest := ⟨{lean_string(request_digest)}⟩

def {cert_name} : Certificate where
  requestDigest := ⟨{lean_string(request_digest)}⟩
  operation := {_OP_LEAN[op]}
  domainConditions := {domains}

theorem {binding_decl} :
    {req_name}.requestDigest = ⟨{lean_string(request_digest)}⟩ := by
  native_decide

theorem {decl} : Claim.proposition {req_name}.claim :=
  replaySound
    {req_name}
    {cert_name}
    (by native_decide : checkBool {req_name} {cert_name} = true)

#print axioms {binding_decl}
#print axioms {decl}
"""


PLUGIN = FormalRationalCalculusPlugin()
register_plugin(PLUGIN)


def generate_exact_formal_rational_calculus_module(
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
