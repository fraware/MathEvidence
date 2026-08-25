"""Exact analytic calculus plugin — whitelist only.

Supported theorem forms with existing Lean decls:
  checkDeriv_sound, checkDerivWithin_sound, checkAntideriv_sound, checkODE_sound.
Unsupported claims fail closed. Numerical calculus remains evidence-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adapters.common.exact_replay.lean_syntax import (
    canonicalize_rat,
    lean_nat,
    lean_qq,
    lean_string,
    matching_copy,
    parse_int_string,
    reject_float_payload,
    safe_ident,
    validate_digest,
    validate_schema_version,
    validate_semver,
)
from adapters.common.exact_replay.pipeline import CanonicalCandidate, ReplayIR
from adapters.common.exact_replay.registry import register_plugin
from adapters.common.limits import ResourceLimits

CAPABILITY = "analysis.analytic_calculus"
GENERATOR_ID = "mathevidence.exact_analytic_calculus"
GENERATOR_VERSION = "0.1.0"
GRAMMAR_VERSION = "0.1.0"
VERIFIER = "mathevidence-declaration-identity"

WHITELIST_KINDS = frozenset(
    {"derivative", "derivativeWithin", "antiderivative", "odeCandidate"}
)
_MAX_DEPTH = 64
_MAX_POW_EXP = 1_000_000


def _parse_qq(value: Any, *, what: str) -> tuple[int, int]:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{what}: floats/bools rejected")
    if isinstance(value, int):
        return canonicalize_rat(value, 1)
    if isinstance(value, str):
        if "/" in value:
            num_s, den_s = value.split("/", 1)
            return canonicalize_rat(
                parse_int_string(num_s, what=f"{what}.num"),
                parse_int_string(den_s, what=f"{what}.den"),
            )
        return canonicalize_rat(parse_int_string(value, what=what), 1)
    if isinstance(value, dict) and value.get("tag") == "rat":
        return canonicalize_rat(
            parse_int_string(value.get("num"), what=f"{what}.num"),
            parse_int_string(value.get("den"), what=f"{what}.den"),
        )
    raise ValueError(f"{what}: unsupported rational encoding")


def _validate_analytic_expr(expr: Any, *, what: str, depth: int = 1) -> dict[str, Any]:
    if depth > _MAX_DEPTH:
        raise ValueError(f"{what}: nesting exceeds {_MAX_DEPTH}")
    if not isinstance(expr, dict):
        raise ValueError(f"{what} must be an object")
    tag = expr.get("tag")
    if tag == "variable":
        idx = expr.get("idx")
        if idx != 0:
            raise ValueError(f"{what}: only univariate variable index 0 is whitelisted")
        return {"tag": "variable", "idx": 0}
    if tag == "const":
        num, den = _parse_qq(expr.get("value"), what=f"{what}.value")
        return {"tag": "const", "num": num, "den": den}
    if tag in {"add", "sub", "mul", "div"}:
        left_key, right_key = ("lhs", "rhs") if "lhs" in expr else ("num", "den")
        if tag != "div":
            left_key, right_key = "lhs", "rhs"
        else:
            if "lhs" in expr:
                left_key, right_key = "lhs", "rhs"
            else:
                left_key, right_key = "num", "den"
        return {
            "tag": tag,
            "lhs": _validate_analytic_expr(expr[left_key], what=f"{what}.{left_key}", depth=depth + 1),
            "rhs": _validate_analytic_expr(expr[right_key], what=f"{what}.{right_key}", depth=depth + 1),
        }
    if tag in {"inv", "neg", "sin", "cos", "exp", "log"}:
        return {
            "tag": tag,
            "arg": _validate_analytic_expr(expr.get("arg"), what=f"{what}.arg", depth=depth + 1),
        }
    if tag == "pow":
        exp = expr.get("exp")
        if isinstance(exp, bool) or not isinstance(exp, int) or exp < 0:
            raise ValueError(f"{what}.exp must be a nonnegative int")
        if exp > _MAX_POW_EXP:
            raise ValueError(f"{what}.exp exceeds maximum {_MAX_POW_EXP}")
        return {
            "tag": "pow",
            "base": _validate_analytic_expr(expr.get("base"), what=f"{what}.base", depth=depth + 1),
            "exp": exp,
        }
    raise ValueError(f"{what}: unsupported analytic constructor {tag!r}")


def _lean_analytic_expr(expr: dict[str, Any]) -> str:
    tag = expr["tag"]
    if tag == "variable":
        return "Expr.variable 0"
    if tag == "const":
        return f"Expr.const {lean_qq(expr['num'], expr['den'])}"
    if tag in {"add", "sub", "mul", "div"}:
        ctor = {
            "add": "Expr.add",
            "sub": "Expr.sub",
            "mul": "Expr.mul",
            "div": "Expr.div",
        }[tag]
        return f"{ctor} ({_lean_analytic_expr(expr['lhs'])}) ({_lean_analytic_expr(expr['rhs'])})"
    if tag in {"inv", "neg", "sin", "cos", "exp", "log"}:
        ctor = {
            "inv": "Expr.inv",
            "neg": "Expr.neg",
            "sin": "Expr.sin",
            "cos": "Expr.cos",
            "exp": "Expr.exp",
            "log": "Expr.log",
        }[tag]
        return f"{ctor} ({_lean_analytic_expr(expr['arg'])})"
    if tag == "pow":
        return f"Expr.pow ({_lean_analytic_expr(expr['base'])}) {lean_nat(int(expr['exp']))}"
    raise ValueError(f"unsupported tag {tag!r}")


def _validate_proof(proof: Any, *, what: str, depth: int = 1) -> dict[str, Any]:
    if depth > _MAX_DEPTH:
        raise ValueError(f"{what}: proof nesting exceeds {_MAX_DEPTH}")
    if not isinstance(proof, dict):
        raise ValueError(f"{what} must be an object")
    tag = proof.get("tag")
    if tag in {"variable", "const"}:
        return {"tag": tag}
    if tag in {"neg", "sin", "exp"}:
        return {"tag": tag, "p": _validate_proof(proof.get("p"), what=f"{what}.p", depth=depth + 1)}
    if tag in {"add", "sub", "mul"}:
        return {
            "tag": tag,
            "p": _validate_proof(proof.get("p"), what=f"{what}.p", depth=depth + 1),
            "q": _validate_proof(proof.get("q"), what=f"{what}.q", depth=depth + 1),
        }
    if tag in {"inv", "log"}:
        oid = proof.get("obligationId")
        if isinstance(oid, bool) or not isinstance(oid, int) or oid < 0:
            raise ValueError(f"{what}.obligationId invalid")
        return {
            "tag": tag,
            "p": _validate_proof(proof.get("p"), what=f"{what}.p", depth=depth + 1),
            "obligationId": oid,
        }
    if tag == "div":
        oid = proof.get("obligationId")
        if isinstance(oid, bool) or not isinstance(oid, int) or oid < 0:
            raise ValueError(f"{what}.obligationId invalid")
        return {
            "tag": tag,
            "p": _validate_proof(proof.get("p"), what=f"{what}.p", depth=depth + 1),
            "q": _validate_proof(proof.get("q"), what=f"{what}.q", depth=depth + 1),
            "obligationId": oid,
        }
    if tag == "pow":
        k = proof.get("k")
        if isinstance(k, bool) or not isinstance(k, int) or k < 0:
            raise ValueError(f"{what}.k invalid")
        if k > _MAX_POW_EXP:
            raise ValueError(f"{what}.k exceeds maximum {_MAX_POW_EXP}")
        return {
            "tag": tag,
            "k": k,
            "p": _validate_proof(proof.get("p"), what=f"{what}.p", depth=depth + 1),
        }
    raise ValueError(f"{what}: unsupported DerivProof tag {tag!r}")


def _lean_proof(proof: dict[str, Any]) -> str:
    tag = proof["tag"]
    if tag in {"variable", "const"}:
        return f"DerivProof.{tag}"
    if tag in {"neg", "sin", "exp"}:
        return f"DerivProof.{tag} ({_lean_proof(proof['p'])})"
    if tag in {"add", "sub", "mul"}:
        return f"DerivProof.{tag} ({_lean_proof(proof['p'])}) ({_lean_proof(proof['q'])})"
    if tag in {"inv", "log"}:
        return f"DerivProof.{tag} ({_lean_proof(proof['p'])}) {lean_nat(int(proof['obligationId']))}"
    if tag == "div":
        return (
            f"DerivProof.div ({_lean_proof(proof['p'])}) ({_lean_proof(proof['q'])}) "
            f"{lean_nat(int(proof['obligationId']))}"
        )
    if tag == "pow":
        return f"DerivProof.pow {lean_nat(int(proof['k']))} ({_lean_proof(proof['p'])})"
    raise ValueError(f"unsupported proof tag {tag!r}")


def _validate_obligation(obl: Any, *, what: str) -> dict[str, Any]:
    if not isinstance(obl, dict):
        raise ValueError(f"{what} must be an object")
    tag = obl.get("tag")
    if tag in {"nonzero", "positive"}:
        return {
            "tag": tag,
            "expr": _validate_analytic_expr(obl.get("expr"), what=f"{what}.expr"),
        }
    if tag == "member":
        # Whitelist only Set.univ membership.
        domain = obl.get("domain")
        if domain not in {"univ", "Set.univ", None} and domain != {"tag": "univ"}:
            raise ValueError(f"{what}: only Set.univ membership is whitelisted")
        return {
            "tag": "member",
            "domain": "univ",
            "expr": _validate_analytic_expr(obl.get("expr"), what=f"{what}.expr"),
        }
    raise ValueError(f"{what}: unsupported DomainObligation {tag!r}")


def _lean_obligation(obl: dict[str, Any]) -> str:
    if obl["tag"] == "nonzero":
        return f"DomainObligation.nonzero ({_lean_analytic_expr(obl['expr'])})"
    if obl["tag"] == "positive":
        return f"DomainObligation.positive ({_lean_analytic_expr(obl['expr'])})"
    return f"DomainObligation.member Set.univ ({_lean_analytic_expr(obl['expr'])})"


def _obligation_binder(index: int, obl: dict[str, Any]) -> tuple[str, str]:
    """Return (binder, proof_term) for SatisfiesObligations reconstruction."""
    name = f"h_obl_{index}"
    if obl["tag"] == "nonzero":
        expr = _lean_analytic_expr(obl["expr"])
        binder = f"({name} : ({expr}).interpret x ≠ 0)"
        proof = f"simpa [DomainObligation.holds, Expr.interpret] using {name}"
        return binder, proof
    if obl["tag"] == "positive":
        expr = _lean_analytic_expr(obl["expr"])
        binder = f"({name} : 0 < ({expr}).interpret x)"
        proof = f"simpa [DomainObligation.holds, Expr.interpret] using {name}"
        return binder, proof
    # member univ is trivial
    name = f"h_obl_{index}"
    binder = f"({name} : True)"
    proof = "trivial"
    return binder, proof


@dataclass(frozen=True)
class AnalyticCalculusPlugin:
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
        matching_copy(request, certificate, "schemaVersion")
        if request.get("capability") != CAPABILITY:
            raise ValueError("exact analytic replay received a different capability")
        if certificate.get("capability") != CAPABILITY:
            raise ValueError("certificate capability does not match request")

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
        if certificate.get("claimsCompleteness") is True:
            raise ValueError("claimsCompleteness must be false")

        kind = request.get("kind")
        cert_kind = certificate.get("kind")
        if cert_kind is not None and cert_kind != kind:
            raise ValueError("certificate kind does not match request kind")
        if kind not in WHITELIST_KINDS:
            raise ValueError(
                f"analytic kind {kind!r} is not on the exact-binding whitelist "
                f"{sorted(WHITELIST_KINDS)}"
            )

        if kind == "odeCandidate":
            if "solution" not in certificate:
                raise ValueError("odeCandidate certificate requires solution")
            if "rhs" not in certificate and "target" not in request:
                raise ValueError("odeCandidate requires certificate.rhs or request.target")
            solution = _validate_analytic_expr(certificate.get("solution"), what="solution")
            rhs = _validate_analytic_expr(
                certificate.get("rhs") if "rhs" in certificate else request.get("target"),
                what="rhs",
            )
            if "rhs" in certificate and "target" in request:
                req_rhs = _validate_analytic_expr(request.get("target"), what="request.target")
                if req_rhs != rhs:
                    raise ValueError("request.target does not match certificate.rhs")
            proof = _validate_proof(
                certificate.get("derivProof") or certificate.get("proof"), what="derivProof"
            )
            ics_raw = certificate.get("initialConditions")
            if ics_raw is None:
                ics_raw = request.get("initialConditions") or []
            if not isinstance(ics_raw, list):
                raise ValueError("initialConditions must be a list")
            ics = []
            for i, ic in enumerate(ics_raw):
                if not isinstance(ic, dict):
                    raise ValueError(f"initialConditions[{i}] must be an object")
                ics.append(
                    {
                        "point": _validate_analytic_expr(ic.get("point"), what=f"ic[{i}].point"),
                        "value": _validate_analytic_expr(ic.get("value"), what=f"ic[{i}].value"),
                    }
                )
            obligations = [
                _validate_obligation(o, what=f"obligations[{i}]")
                for i, o in enumerate(certificate.get("obligations") or [])
            ]
            return CanonicalCandidate(
                capability_id=CAPABILITY,
                capability_version=capability_version,
                request=dict(request),
                certificate=dict(certificate),
                candidate_bundle_digest=candidate_bundle_digest,
                request_digest=request_digest,
                claim_class="soundResult",
                extras={
                    "kind": kind,
                    "solution": solution,
                    "rhs": rhs,
                    "proof": proof,
                    "initial_conditions": ics,
                    "obligations": obligations,
                },
            )

        if "source" not in certificate and "source" not in request:
            raise ValueError("analytic certificate/request requires source")
        if "derivative" not in certificate and "target" not in request:
            raise ValueError("analytic certificate/request requires derivative/target")
        source = _validate_analytic_expr(
            certificate.get("source") if "source" in certificate else request.get("source"),
            what="source",
        )
        derivative = _validate_analytic_expr(
            certificate.get("derivative")
            if "derivative" in certificate
            else request.get("target"),
            what="derivative",
        )
        if "source" in certificate and "source" in request:
            req_source = _validate_analytic_expr(request.get("source"), what="request.source")
            if req_source != source:
                raise ValueError("request.source does not match certificate.source")
        if "derivative" in certificate and "target" in request:
            req_target = _validate_analytic_expr(request.get("target"), what="request.target")
            if req_target != derivative:
                raise ValueError("request.target does not match certificate.derivative")
        proof = _validate_proof(certificate.get("proof"), what="proof")
        obligations = [
            _validate_obligation(o, what=f"obligations[{i}]")
            for i, o in enumerate(certificate.get("obligations") or [])
        ]
        return CanonicalCandidate(
            capability_id=CAPABILITY,
            capability_version=capability_version,
            request=dict(request),
            certificate=dict(certificate),
            candidate_bundle_digest=candidate_bundle_digest,
            request_digest=request_digest,
            claim_class="soundResult",
            extras={
                "kind": kind,
                "source": source,
                "derivative": derivative,
                "proof": proof,
                "obligations": obligations,
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
            ),
            metadata={
                "request_digest": canonical.request_digest,
                "candidate_bundle_digest": canonical.candidate_bundle_digest,
                "kind": canonical.extras["kind"],
            },
        )

    def render(self, ir: ReplayIR) -> str:
        meta = {node[0]: node[1] for node in ir.nodes}
        kind = meta["kind"]
        request_digest = meta["request_digest"]
        candidate_bundle_digest = meta["candidate_bundle_digest"]
        decl = ir.declaration_name
        obligations = list(meta.get("obligations") or [])
        obls_lean = "#[" + ", ".join(_lean_obligation(o) for o in obligations) + "]"
        binders: list[str] = []
        obl_proofs: list[str] = []
        for i, obl in enumerate(obligations):
            binder, proof = _obligation_binder(i, obl)
            binders.append(binder)
            obl_proofs.append(proof)
        binder_str = (" ".join(binders) + " ") if binders else ""
        if not obligations:
            hdom = "(fun i => Fin.elim0 i)"
        else:
            cases = "\n".join(f"    · {p}" for p in obl_proofs)
            hdom = f"(by\n    intro i\n    fin_cases i\n{cases})"

        soundness_fn = {
            "derivative": "checkDeriv_sound",
            "derivativeWithin": "checkDerivWithin_sound",
            "antiderivative": "checkAntideriv_sound",
            "odeCandidate": "checkODE_sound",
        }[kind]

        if kind == "odeCandidate":
            solution = _lean_analytic_expr(meta["solution"])
            rhs = _lean_analytic_expr(meta["rhs"])
            proof = _lean_proof(meta["proof"])
            ics = meta["initial_conditions"]
            if ics:
                ic_parts = []
                for ic in ics:
                    ic_parts.append(
                        "{ point := "
                        f"{_lean_analytic_expr(ic['point'])}, value := {_lean_analytic_expr(ic['value'])} }}"
                    )
                ics_lean = "#[" + ", ".join(ic_parts) + "]"
            else:
                ics_lean = "#[]"
            if obligations:
                raise ValueError(
                    "exact ODE replay currently requires empty obligations "
                    "(domain hypotheses must be binder-bound on Deriv/DerivWithin paths)"
                )
            cert_expr = (
                "{\n"
                f"    requestDigest := ⟨{lean_string(request_digest)}⟩\n"
                f"    solution := {solution}\n"
                f"    rhs := {rhs}\n"
                f"    derivProof := {proof}\n"
                f"    obligations := {obls_lean}\n"
                f"    initialConditions := {ics_lean}\n"
                f"    domain := Set.univ\n"
                f"    claimsCompleteness := false\n"
                "  }"
            )
            # Full CandidateSolvesFirstOrderODE with explicit IC/domain hypotheses.
            # Empty-obligation domain proof mirrors OfflineFixtures.sound_ode_sq.
            if not ics:
                hic_proof = "intro ic hic; cases hic"
            else:
                # Mirror OfflineFixtures.sound_ode_sq: membership forces the
                # concrete InitialCondition, then interpret both sides.
                first = ics[0]
                first_lean = (
                    "{ point := "
                    f"{_lean_analytic_expr(first['point'])}, "
                    f"value := {_lean_analytic_expr(first['value'])} }}"
                )
                hic_proof = (
                    "intro ic hic\n"
                    f"      have : ic = {first_lean} := by\n"
                    "        simp at hic\n"
                    "        exact hic\n"
                    "      subst this\n"
                    "      simp [Expr.interpret]"
                )
                if len(ics) != 1:
                    raise ValueError(
                        "exact ODE replay currently supports a single initial condition"
                    )
            return f"""/-
AUTO-GENERATED -- UNTRUSTED exact-candidate replay source.
moduleName = {ir.module_name}
candidateBundleDigest = {candidate_bundle_digest}
requestDigest = {request_digest}
generatorId = {ir.generator_id}
generatorVersion = {ir.generator_version}
grammarVersion = {ir.grammar_version}
kind = {kind}
whitelist = checkODE_sound
-/
import MathEvidence.Checkers.AnalyticCalculus.Soundness
import MathEvidence.Checkers.AnalyticCalculus.Spec
import MathEvidence.IR.AnalyticExpr.Domain
import MathEvidence.IR.AnalyticExpr.Syntax

open MathEvidence.Core
open MathEvidence.IR.AnalyticExpr
open MathEvidence.Checkers.AnalyticCalculus

theorem {decl} :
    let cert : ODECertificate := {cert_expr}
    CandidateSolvesFirstOrderODE
      cert.solution.interpret cert.rhs.interpret
      cert.domain
      (cert.initialConditions.toList.map InitialCondition.asPair) := by
  let cert : ODECertificate := {cert_expr}
  have hCheck : checkODE cert = true := by
    native_decide
  exact checkODE_sound cert hCheck
    (fun _ _ i => Fin.elim0 i)
    (by
      {hic_proof})

#print axioms {decl}
"""

        source = _lean_analytic_expr(meta["source"])
        derivative = _lean_analytic_expr(meta["derivative"])
        proof = _lean_proof(meta["proof"])
        cert_type = "AntiderivCertificate" if kind == "antiderivative" else "DerivCertificate"
        check_fn = "checkAntideriv" if kind == "antiderivative" else "checkDeriv"
        cert_expr = (
            "{\n"
            f"    requestDigest := ⟨{lean_string(request_digest)}⟩\n"
            f"    source := {source}\n"
            f"    derivative := {derivative}\n"
            f"    proof := {proof}\n"
            f"    obligations := {obls_lean}\n"
            f"    claimsCompleteness := false\n"
            "  }"
        )
        if kind == "derivativeWithin":
            conclusion = (
                f"HasDerivWithinAt ({source}).interpret "
                f"(({derivative}).interpret x) Set.univ x"
            )
            apply = (
                f"exact checkDerivWithin_sound cert Set.univ x hCheck {hdom} "
                f"(trivial : x ∈ (Set.univ : Set ℝ))"
            )
        else:
            conclusion = (
                f"HasDerivAt ({source}).interpret (({derivative}).interpret x) x"
            )
            apply = f"exact {soundness_fn} cert x hCheck {hdom}"
        return f"""/-
AUTO-GENERATED -- UNTRUSTED exact-candidate replay source.
moduleName = {ir.module_name}
candidateBundleDigest = {candidate_bundle_digest}
requestDigest = {request_digest}
generatorId = {ir.generator_id}
generatorVersion = {ir.generator_version}
grammarVersion = {ir.grammar_version}
kind = {kind}
whitelist = {soundness_fn}
-/
import MathEvidence.Checkers.AnalyticCalculus.Soundness
import MathEvidence.IR.AnalyticExpr.Domain
import MathEvidence.IR.AnalyticExpr.Syntax

open MathEvidence.Core
open MathEvidence.IR.AnalyticExpr
open MathEvidence.Checkers.AnalyticCalculus

theorem {decl} (x : ℝ) {binder_str}:
    {conclusion} := by
  let cert : {cert_type} := {cert_expr}
  have hCheck : {check_fn} cert = true := by
    native_decide
  {apply}

#print axioms {decl}
"""


PLUGIN = AnalyticCalculusPlugin()
register_plugin(PLUGIN)


def generate_exact_analytic_calculus_module(
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
