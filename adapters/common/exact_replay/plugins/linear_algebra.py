"""Exact linear-algebra plugin (SPEC-05).

Operations enabled independently via registry ``exactBinding.operations``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adapters.common.exact_replay.lean_syntax import (
    canonicalize_rat,
    lean_nat,
    lean_rat_lit,
    lean_string,
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
from agent.api.assurance_policy import exact_binding, load_assurance_policy

CAPABILITY = "algebra.linear_algebra"
GENERATOR_ID = "mathevidence.exact_linear_algebra"
GENERATOR_VERSION = "0.1.0"
GRAMMAR_VERSION = "0.1.0"
VERIFIER = "mathevidence-declaration-identity"

OPERATIONS = frozenset(
    {"inverse_witness", "system_solution", "kernel_vector", "det_identity"}
)
_OP_LEAN = {
    "inverse_witness": ".inverseWitness",
    "system_solution": ".systemSolution",
    "kernel_vector": ".kernelVector",
    "det_identity": ".detIdentity",
}
_MAX_DIM = 64


def _enabled_operations() -> frozenset[str]:
    policy = load_assurance_policy(CAPABILITY)
    binding = exact_binding(policy)
    ops = binding.get("operations")
    if isinstance(ops, dict) and ops:
        enabled = {
            name
            for name, meta in ops.items()
            if isinstance(meta, dict) and meta.get("exactBindingSupported") is True
        }
        return frozenset(enabled)
    # Generator complete: default to inventory when registry omits the map.
    return OPERATIONS


def _parse_rat_lit(value: Any, *, what: str) -> tuple[int, int]:
    if not isinstance(value, dict) or value.get("tag") != "rat":
        raise ValueError(f"{what} must be tag=rat")
    num = parse_int_string(value.get("num"), what=f"{what}.num")
    den = parse_nat_string(value.get("den"), what=f"{what}.den")
    if den == 0:
        raise ValueError(f"{what}: den=0 rejected before Lean")
    return canonicalize_rat(num, den)


def _parse_matrix(value: Any, *, what: str) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("tag") != "matrix":
        raise ValueError(f"{what} must be a matrix object")
    rows = value.get("rows")
    cols = value.get("cols")
    if not isinstance(rows, int) or isinstance(rows, bool) or rows < 1 or rows > _MAX_DIM:
        raise ValueError(f"{what}.rows out of range")
    if not isinstance(cols, int) or isinstance(cols, bool) or cols < 1 or cols > _MAX_DIM:
        raise ValueError(f"{what}.cols out of range")
    entries = value.get("entries")
    if not isinstance(entries, list) or len(entries) != rows:
        raise ValueError(f"{what}.entries must have length rows")
    parsed: list[list[tuple[int, int]]] = []
    for r, row in enumerate(entries):
        if not isinstance(row, list) or len(row) != cols:
            raise ValueError(f"{what}.entries[{r}] must have length cols")
        parsed.append([_parse_rat_lit(cell, what=f"{what}.entries[{r}][{c}]") for c, cell in enumerate(row)])
    return {"tag": "matrix", "rows": rows, "cols": cols, "entries": parsed}


def _parse_vector(value: Any, *, what: str, expected_len: int | None = None) -> list[tuple[int, int]]:
    if not isinstance(value, list):
        raise ValueError(f"{what} must be a list")
    if expected_len is not None and len(value) != expected_len:
        raise ValueError(f"{what} length mismatch")
    if len(value) > _MAX_DIM:
        raise ValueError(f"{what} exceeds max dimension")
    return [_parse_rat_lit(item, what=f"{what}[{i}]") for i, item in enumerate(value)]


def _lean_matrix(matrix: dict[str, Any]) -> str:
    rows = matrix["rows"]
    cols = matrix["cols"]
    row_exprs: list[str] = []
    for row in matrix["entries"]:
        cells = ", ".join(lean_rat_lit(n, d) for n, d in row)
        row_exprs.append(f"[{cells}]")
    entries = "[" + ", ".join(row_exprs) + "]"
    return (
        "{ nrows := "
        f"{lean_nat(rows)}, ncols := {lean_nat(cols)}, entries := {entries} }}"
    )


def _lean_vector(vector: list[tuple[int, int]]) -> str:
    return "[" + ", ".join(lean_rat_lit(n, d) for n, d in vector) + "]"


@dataclass(frozen=True)
class LinearAlgebraPlugin:
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
            raise ValueError("exact LA replay received a different capability")
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
            raise ValueError(f"unsupported LA operation: {operation!r}")
        if certificate.get("operation") != operation:
            raise ValueError("certificate operation does not match request")
        if operation not in _enabled_operations():
            raise ValueError(f"operation {operation!r} is not exactBinding-enabled")

        requested = request.get("requestedClaim")
        if operation == "det_identity":
            if requested != "soundResult":
                raise ValueError("det_identity requires requestedClaim soundResult")
            claim_class = "soundResult"
        else:
            if requested != "witness":
                raise ValueError(f"{operation} requires requestedClaim witness")
            claim_class = "witness"

        matrix = _parse_matrix(request.get("matrix"), what="matrix")
        rhs: list[tuple[int, int]] | None = None
        claimed_det: tuple[int, int] | None = None
        inverse: dict[str, Any] | None = None
        vector: list[tuple[int, int]] | None = None

        if operation == "system_solution":
            rhs = _parse_vector(request.get("rhs"), what="rhs", expected_len=matrix["rows"])
            vector = _parse_vector(
                certificate.get("vector"), what="vector", expected_len=matrix["cols"]
            )
        elif operation == "kernel_vector":
            vector = _parse_vector(
                certificate.get("vector"), what="vector", expected_len=matrix["cols"]
            )
        elif operation == "inverse_witness":
            inverse = _parse_matrix(certificate.get("inverse"), what="inverse")
            if inverse["rows"] != matrix["rows"] or inverse["cols"] != matrix["cols"]:
                raise ValueError("inverse dimensions must match matrix")
            if matrix["rows"] != matrix["cols"]:
                raise ValueError("inverse_witness requires a square matrix")
        elif operation == "det_identity":
            if matrix["rows"] != matrix["cols"]:
                raise ValueError("det_identity requires a square matrix")
            claimed_det = _parse_rat_lit(request.get("claimedDet"), what="claimedDet")

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
                "matrix": matrix,
                "rhs": rhs,
                "claimed_det": claimed_det,
                "inverse": inverse,
                "vector": vector,
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
                ("operation", canonical.extras["operation"]),
                ("matrix", canonical.extras["matrix"]),
                ("rhs", canonical.extras["rhs"]),
                ("claimed_det", canonical.extras["claimed_det"]),
                ("inverse", canonical.extras["inverse"]),
                ("vector", canonical.extras["vector"]),
                ("claim_class", canonical.claim_class),
                ("request_digest", canonical.request_digest),
                ("candidate_bundle_digest", canonical.candidate_bundle_digest),
            ),
            metadata={
                "request_digest": canonical.request_digest,
                "candidate_bundle_digest": canonical.candidate_bundle_digest,
                "operation": canonical.extras["operation"],
            },
        )

    def render(self, ir: ReplayIR) -> str:
        meta = {node[0]: node[1] for node in ir.nodes}
        operation = meta["operation"]
        matrix_lean = _lean_matrix(meta["matrix"])
        op_lean = _OP_LEAN[operation]
        claim_class = ".soundResult" if meta["claim_class"] == "soundResult" else ".witness"
        rhs_lean = _lean_vector(meta["rhs"]) if meta["rhs"] is not None else "[]"
        if meta["claimed_det"] is not None:
            n, d = meta["claimed_det"]
            claimed_lean = f"some ({lean_rat_lit(n, d)})"
        else:
            claimed_lean = "none"
        if meta["inverse"] is not None:
            inverse_lean = f"some ({_lean_matrix(meta['inverse'])})"
        else:
            inverse_lean = "none"
        if meta["vector"] is not None:
            vector_lean = f"some ({_lean_vector(meta['vector'])})"
        else:
            vector_lean = "none"
        request_digest = meta["request_digest"]
        candidate_bundle_digest = meta["candidate_bundle_digest"]
        decl = ir.declaration_name
        claim_name = f"{decl}_claim"
        req_name = f"{decl}_req"
        cert_name = f"{decl}_cert"
        binding_decl = f"{decl}_request_binding"

        claim_fields = (
            f"  operation := {op_lean}\n"
            f"  matrix := {matrix_lean}\n"
            f"  rhs := {rhs_lean}\n"
            f"  claimedDet := {claimed_lean}\n"
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
operation = {operation}
-/
import MathEvidence.Checkers.LinearAlgebra.ReplaySound
import MathEvidence.IR.MatrixExpr.Syntax

open MathEvidence.Core
open MathEvidence.IR.MatrixExpr
open MathEvidence.Checkers.LinearAlgebra

def {claim_name} : Claim where
{claim_fields}

def {req_name} : Request where
  claim := {claim_name}
  requestDigest := ⟨{lean_string(request_digest)}⟩

def {cert_name} : Certificate where
  requestDigest := ⟨{lean_string(request_digest)}⟩
  inverse := {inverse_lean}
  vector := {vector_lean}

theorem {binding_decl} :
    {req_name}.requestDigest = ⟨{lean_string(request_digest)}⟩ := by
  native_decide

theorem {decl} : Claim.proposition {req_name}.claim {cert_name}.inverse {cert_name}.vector :=
  replaySound
    {req_name}
    {cert_name}
    (by native_decide : checkBool {req_name} {cert_name} = true)

#print axioms {binding_decl}
#print axioms {decl}
"""


PLUGIN = LinearAlgebraPlugin()
register_plugin(PLUGIN)


def generate_exact_linear_algebra_module(
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
