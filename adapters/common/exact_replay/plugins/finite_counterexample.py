"""Exact finite-counterexample / certified-refutation plugin (SPEC-06).

Valid witness => outcome polarity ``refuted`` (never ``proved``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adapters.common.exact_replay.lean_syntax import (
    lean_int,
    lean_nat,
    lean_string,
    lean_string_list,
    matching_copy,
    parse_int_string,
    parse_nat_string,
    reject_float_payload,
    safe_ident,
    validate_digest,
    validate_schema_version,
    validate_semver,
)
from adapters.common.exact_replay.pipeline import CanonicalCandidate, ReplayIR
from adapters.common.exact_replay.registry import register_plugin
from adapters.common.limits import ResourceLimits

CAPABILITY = "logic.finite_counterexample"
GENERATOR_ID = "mathevidence.exact_finite_counterexample"
GENERATOR_VERSION = "0.1.0"
GRAMMAR_VERSION = "0.1.0"
VERIFIER = "mathevidence-declaration-identity"
_MAX_DOMAIN = 1024
_MAX_TERM_DEPTH = 64


def _lean_val(val: dict[str, Any]) -> str:
    tag = val["tag"]
    if tag == "bool":
        return f"Val.bool {'true' if val['v'] else 'false'}"
    if tag == "nat":
        return f"Val.nat {lean_nat(int(val['v']))}"
    if tag == "int":
        return f"Val.int {lean_int(int(val['v']))}"
    raise ValueError(f"unsupported Val tag {tag!r}")


def _lean_term(term: dict[str, Any]) -> str:
    tag = term["tag"]
    if tag == "var":
        return f"Term.var {lean_nat(int(term['idx']))}"
    if tag == "lit":
        return f"Term.lit ({_lean_val(term['v'])})"
    if tag == "neg":
        return f"Term.neg ({_lean_term(term['e'])})"
    if tag in {"add", "sub", "mul"}:
        ctor = {"add": "Term.add", "sub": "Term.sub", "mul": "Term.mul"}[tag]
        return f"{ctor} ({_lean_term(term['left'])}) ({_lean_term(term['right'])})"
    raise ValueError(f"unsupported Term tag {tag!r}")


def _lean_pred(pred: dict[str, Any]) -> str:
    tag = pred["tag"]
    if tag in {"eq", "ne", "le", "lt"}:
        ctor = {
            "eq": "Pred.eq",
            "ne": "Pred.ne",
            "le": "Pred.le",
            "lt": "Pred.lt",
        }[tag]
        return f"{ctor} ({_lean_term(pred['left'])}) ({_lean_term(pred['right'])})"
    if tag == "not":
        return f"Pred.not ({_lean_pred(pred['e'])})"
    if tag in {"and", "or"}:
        ctor = "Pred.and" if tag == "and" else "Pred.or"
        return f"{ctor} ({_lean_pred(pred['left'])}) ({_lean_pred(pred['right'])})"
    raise ValueError(f"unsupported Pred tag {tag!r}")


def _validate_val(value: Any, *, what: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{what} must be an object")
    tag = value.get("tag")
    if tag == "bool":
        v = value.get("v")
        if not isinstance(v, bool):
            raise ValueError(f"{what}.v must be bool")
        return {"tag": "bool", "v": v}
    if tag == "nat":
        n = value.get("v")
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            # also accept string
            if isinstance(n, str):
                n = parse_nat_string(n, what=f"{what}.v")
            else:
                raise ValueError(f"{what}.v must be a nat")
        return {"tag": "nat", "v": n}
    if tag == "int":
        n = value.get("v")
        if isinstance(n, bool):
            raise ValueError(f"{what}: bool rejected")
        if isinstance(n, float):
            raise ValueError(f"{what}: float rejected")
        if isinstance(n, str):
            n = parse_int_string(n, what=f"{what}.v")
        elif not isinstance(n, int):
            raise ValueError(f"{what}.v must be an int")
        return {"tag": "int", "v": n}
    raise ValueError(f"{what}: unsupported val tag {tag!r}")


def _validate_term(term: Any, *, domain_count: int, what: str, depth: int = 1) -> dict[str, Any]:
    if depth > _MAX_TERM_DEPTH:
        raise ValueError(f"{what}: term nesting exceeds {_MAX_TERM_DEPTH}")
    if not isinstance(term, dict):
        raise ValueError(f"{what} must be an object")
    tag = term.get("tag")
    if tag == "var":
        idx = term.get("idx")
        if isinstance(idx, bool) or not isinstance(idx, int) or idx < 0 or idx >= domain_count:
            raise ValueError(f"{what}.idx out of domain range")
        return {"tag": "var", "idx": idx}
    if tag == "lit":
        return {"tag": "lit", "v": _validate_val(term.get("v"), what=f"{what}.v")}
    if tag == "neg":
        return {"tag": "neg", "e": _validate_term(term.get("e"), domain_count=domain_count, what=f"{what}.e", depth=depth + 1)}
    if tag in {"add", "sub", "mul"}:
        return {
            "tag": tag,
            "left": _validate_term(term.get("left"), domain_count=domain_count, what=f"{what}.left", depth=depth + 1),
            "right": _validate_term(term.get("right"), domain_count=domain_count, what=f"{what}.right", depth=depth + 1),
        }
    raise ValueError(f"{what}: unsupported term constructor {tag!r}")


def _validate_pred(pred: Any, *, domain_count: int, what: str, depth: int = 1) -> dict[str, Any]:
    if depth > _MAX_TERM_DEPTH:
        raise ValueError(f"{what}: predicate nesting exceeds {_MAX_TERM_DEPTH}")
    if not isinstance(pred, dict):
        raise ValueError(f"{what} must be an object")
    tag = pred.get("tag")
    if tag in {"eq", "ne", "le", "lt"}:
        return {
            "tag": tag,
            "left": _validate_term(pred.get("left"), domain_count=domain_count, what=f"{what}.left", depth=depth + 1),
            "right": _validate_term(pred.get("right"), domain_count=domain_count, what=f"{what}.right", depth=depth + 1),
        }
    if tag == "not":
        return {
            "tag": "not",
            "e": _validate_pred(pred.get("e"), domain_count=domain_count, what=f"{what}.e", depth=depth + 1),
        }
    if tag in {"and", "or"}:
        return {
            "tag": tag,
            "left": _validate_pred(pred.get("left"), domain_count=domain_count, what=f"{what}.left", depth=depth + 1),
            "right": _validate_pred(pred.get("right"), domain_count=domain_count, what=f"{what}.right", depth=depth + 1),
        }
    raise ValueError(f"{what}: unsupported pred constructor {tag!r}")


def _validate_domain(domain: Any, *, what: str) -> dict[str, Any]:
    if not isinstance(domain, dict):
        raise ValueError(f"{what} must be an object")
    ty = domain.get("ty")
    if ty not in {"bool", "nat", "int"}:
        raise ValueError(f"{what}.ty unsupported")
    out: dict[str, Any] = {"ty": ty}
    if "bound" in domain and domain["bound"] is not None:
        bound = domain["bound"]
        if isinstance(bound, bool) or not isinstance(bound, int) or bound < 0:
            raise ValueError(f"{what}.bound must be a nonnegative int")
        if bound > _MAX_DOMAIN:
            raise ValueError(f"{what}.bound exceeds max domain cardinality")
        out["bound"] = bound
    else:
        out["bound"] = None
    # Dependent bounds are out of the compact exact wire for Phase 2 fail-closed:
    # schema currently only lists ty/bound; reject unexpected keys that would
    # silently drop binder terms.
    for key in domain:
        if key not in {"ty", "bound"}:
            raise ValueError(f"{what}: unsupported domain field {key!r}")
    if ty == "bool":
        return out
    if out["bound"] is None:
        raise ValueError(f"{what}: non-bool domains require an explicit bound for exact binding")
    return out


def _lean_domain(domain: dict[str, Any]) -> str:
    ty = domain["ty"]
    ty_lean = {"bool": ".bool", "nat": ".nat", "int": ".int"}[ty]
    if ty == "bool":
        return "{ ty := .bool }"
    return f"{{ ty := {ty_lean}, bound := some {lean_nat(int(domain['bound']))} }}"


def _witness_in_domain(witness: list[dict[str, Any]], domains: list[dict[str, Any]]) -> None:
    if len(witness) != len(domains):
        raise ValueError("witness arity must equal domain count")
    for index, (val, dom) in enumerate(zip(witness, domains)):
        if val["tag"] != dom["ty"]:
            raise ValueError(f"witness[{index}] type mismatch with domain")
        if dom["ty"] == "bool":
            continue
        bound = int(dom["bound"])
        if dom["ty"] == "nat":
            if int(val["v"]) > bound:
                raise ValueError(f"witness[{index}] out of nat domain 0..{bound}")
        elif dom["ty"] == "int":
            if abs(int(val["v"])) > bound:
                raise ValueError(f"witness[{index}] out of int domain -{bound}..{bound}")


@dataclass(frozen=True)
class FiniteCounterexamplePlugin:
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
            raise ValueError("exact CEX replay received a different capability")
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

        requested = request.get("requestedClaim")
        # Sampling / candidate-only must not mint theorems (fail closed).
        if requested == "candidate":
            raise ValueError("candidate claim cannot mint certified refutation")
        if requested not in {"refutation", "witness"}:
            raise ValueError(
                "theorem-producing CEX replay requires requestedClaim refutation "
                "(or witness mapped to refutation polarity); "
                f"got {requested!r}"
            )

        predicate = request.get("predicate")
        if not isinstance(predicate, dict):
            raise ValueError("request.predicate must be an object")
        var_names = predicate.get("varNames")
        if not isinstance(var_names, list) or not var_names or not all(isinstance(n, str) for n in var_names):
            raise ValueError("predicate.varNames must be a nonempty string list")
        domains_raw = predicate.get("domains")
        if not isinstance(domains_raw, list) or len(domains_raw) != len(var_names):
            raise ValueError("predicate.domains arity must equal varNames")
        domains = [
            _validate_domain(d, what=f"domains[{i}]") for i, d in enumerate(domains_raw)
        ]
        pred = _validate_pred(
            predicate.get("pred"), domain_count=len(domains), what="predicate.pred"
        )

        witness_obj = certificate.get("witness")
        if not isinstance(witness_obj, dict):
            raise ValueError("certificate.witness must be an object")
        assignment = witness_obj.get("assignment")
        if not isinstance(assignment, list) or not assignment:
            raise ValueError(
                "no-witness / empty assignment cannot mint proved or refuted theorems"
            )
        witness = [
            _validate_val(item, what=f"witness.assignment[{i}]")
            for i, item in enumerate(assignment)
        ]
        _witness_in_domain(witness, domains)

        return CanonicalCandidate(
            capability_id=CAPABILITY,
            capability_version=capability_version,
            request=dict(request),
            certificate=dict(certificate),
            candidate_bundle_digest=candidate_bundle_digest,
            request_digest=request_digest,
            claim_class="refutation",
            extras={
                "var_names": list(var_names),
                "domains": domains,
                "pred": pred,
                "witness": witness,
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
                ("domains", tuple(canonical.extras["domains"])),
                ("pred", canonical.extras["pred"]),
                ("witness", tuple(canonical.extras["witness"])),
                ("request_digest", canonical.request_digest),
                ("candidate_bundle_digest", canonical.candidate_bundle_digest),
            ),
            metadata={
                "request_digest": canonical.request_digest,
                "candidate_bundle_digest": canonical.candidate_bundle_digest,
                "outcome": "refuted",
            },
        )

    def render(self, ir: ReplayIR) -> str:
        meta = {node[0]: node[1] for node in ir.nodes}
        var_names = lean_string_list(list(meta["var_names"]))
        domains = "[" + ", ".join(_lean_domain(d) for d in meta["domains"]) + "]"
        pred = _lean_pred(meta["pred"])
        witness = "[" + ", ".join(_lean_val(v) for v in meta["witness"]) + "]"
        request_digest = meta["request_digest"]
        candidate_bundle_digest = meta["candidate_bundle_digest"]
        decl = ir.declaration_name
        claim_name = f"{decl}_claim"
        req_name = f"{decl}_req"
        cert_name = f"{decl}_cert"
        binding_decl = f"{decl}_request_binding"
        claim_fields = (
            f"  varNames := {var_names}\n"
            f"  domains := {domains}\n"
            f"  pred := {pred}\n"
            f"  claimClass := .refutation"
        )
        return f"""/-
AUTO-GENERATED -- UNTRUSTED exact-candidate replay source.
moduleName = {ir.module_name}
candidateBundleDigest = {candidate_bundle_digest}
requestDigest = {request_digest}
generatorId = {ir.generator_id}
generatorVersion = {ir.generator_version}
grammarVersion = {ir.grammar_version}
outcome = refuted
-/
import MathEvidence.Checkers.Counterexample.ReplaySound
import MathEvidence.IR.FinitePredicate.Syntax

open MathEvidence.Core
open MathEvidence.IR.FinitePredicate
open MathEvidence.Checkers.Counterexample

def {claim_name} : Claim where
{claim_fields}

def {req_name} : Request where
  claim := {claim_name}
  requestDigest := ⟨{lean_string(request_digest)}⟩

def {cert_name} : Certificate where
  requestDigest := ⟨{lean_string(request_digest)}⟩
  witness := {witness}

theorem {binding_decl} :
    {req_name}.requestDigest = ⟨{lean_string(request_digest)}⟩ := by
  native_decide

/-- Certified refutation: predicate is false at the bound witness (never proved). -/
theorem {decl} : Claim.proposition {req_name}.claim {cert_name}.witness :=
  replaySound
    {req_name}
    {cert_name}
    (by native_decide : checkBool {req_name} {cert_name} = true)

#print axioms {binding_decl}
#print axioms {decl}
"""


PLUGIN = FiniteCounterexamplePlugin()
register_plugin(PLUGIN)


def generate_exact_finite_counterexample_module(
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
