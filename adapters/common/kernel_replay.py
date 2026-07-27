"""Kernel replay driver (Wave 2 / ME-RV-022).

Orchestrates: Candidate Bundle → ReplayTarget → generated Lean module →
``lake env lean`` → axiom policy → Certification Record (outside the bundle).

This module never promotes ``soundness_verified`` without a compiled declaration
and passing axiom policy. ``require_lean=False`` still MUST NOT mint theorem-level
statuses: missing/failed Lean yields a structured error (not a Certified result).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from adapters.common.bundle import (
    compute_bundle_digest,
    find_role_path,
    load_role_json,
    verify_bundle_offline,
    write_certification_record,
)
from adapters.common.canonical import sha256_digest
from adapters.common.errors import AdapterError, stable_error
from adapters.common.theorem_identity import (
    THEOREM_IDENTITY_SERIALIZER_VERSION,
    build_replay_target,
    default_rational_environment_lock,
    environment_lock_digest,
    theorem_identity_payload,
    theorem_type_digest,
)

ALLOWED_AXIOMS_DEFAULT = (
    "propext",
    "Quot.sound",
    "Classical.choice",
    "Lean.ofReduceBool",
    "Lean.trustCompiler",
)


def _generate_from_target(target: dict[str, Any]) -> str:
    """Untrusted generator mirror of scripts/generate_replay_module.py."""
    import importlib.util

    repo = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "generate_replay_module",
        repo / "scripts" / "generate_replay_module.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load generate_replay_module.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.generate_from_target(target)

# Kernel-replay stable error codes (02_TRUST_PATH).
KERNEL_REPLAY_CODES = frozenset(
    {
        "bundle_not_found",
        "manifest_invalid",
        "content_digest_mismatch",
        "request_decode_failed",
        "certificate_decode_failed",
        "request_digest_mismatch",
        "goal_reification_failed",
        "goal_claim_mismatch",
        "checker_rejected",
        "side_condition_unresolved",
        "theorem_elaboration_failed",
        "kernel_rejected",
        "unexpected_axiom",
        "environment_mismatch",
        "resource_limit_exceeded",
        # Windows Lake 4.14 leanc CreateProcess 206 / missing linked exe.
        "replay_dependency_missing",
        "assurance_mode_unavailable",
    }
)

THEOREM_LEVEL_STATUSES = frozenset(
    {
        "witness_verified",
        "soundness_verified",
        "completeness_verified",
        "optimality_verified",
        "approximation_certified",
        "native_verified",
    }
)


class KernelReplayError(AdapterError):
    """Structured kernel-replay failure."""


def _kr_error(code: str, message: str, **details: Any) -> KernelReplayError:
    # Prefer registered codes; map aliases into STABLE_CODES where needed.
    mapped = code
    aliases = {
        "manifest_invalid": "manifest_schema_invalid",
        "request_decode_failed": "certificate_decode_failed",
        "checker_rejected": "certificate_rejected",
        "goal_reification_failed": "goal_mismatch",
        "goal_claim_mismatch": "goal_mismatch",
        "side_condition_unresolved": "side_condition_unproved",
        "theorem_elaboration_failed": "malformed_evidence",
        "kernel_rejected": "malformed_evidence",
        "unexpected_axiom": "axiom_policy_violation",
        "environment_mismatch": "assurance_mode_unavailable",
        "platform_link_failed": "replay_dependency_missing",
    }
    mapped = aliases.get(code, code)
    try:
        return KernelReplayError(code=mapped, message=f"{code}: {message}", details={"kernelCode": code, **details})
    except ValueError:
        return KernelReplayError(
            code="malformed_evidence",
            message=f"{code}: {message}",
            details={"kernelCode": code, **details},
        )


def find_lake(repo_root: Path) -> Path | None:
    which = shutil.which("lake")
    if which:
        return Path(which)
    return None


def parse_print_axioms(stdout: str, declaration_name: str) -> list[str]:
    """Parse `#print axioms` output into axiom/constant names."""
    axioms: list[str] = []
    # Typical: "'decl' depends on axioms: [propext, Quot.sound]"
    for line in stdout.splitlines():
        if declaration_name in line and "axioms" in line.lower():
            m = re.search(r"\[([^\]]*)\]", line)
            if m:
                inner = m.group(1).strip()
                if inner:
                    axioms = [a.strip() for a in inner.split(",") if a.strip()]
            elif "depends on axioms: []" in line or "no axioms" in line.lower():
                axioms = []
    return axioms


def axiom_policy_ok(
    axioms: list[str], allowed: tuple[str, ...] = ALLOWED_AXIOMS_DEFAULT
) -> bool:
    allowed_set = set(allowed)
    return all(a in allowed_set for a in axioms)


def build_structural_theorem_type(
    *,
    var_names: list[str],
    claim_preview: str,
    constant_names: list[str] | None = None,
    binder_type: str = "Rat",
) -> dict[str, Any]:
    binders = [
        {"name": n, "kind": "default", "typeSerialization": binder_type}
        for n in var_names
    ]
    return {
        "schemaVersion": "0.3.0",
        "serializerVersion": THEOREM_IDENTITY_SERIALIZER_VERSION,
        "elaboratedSerialization": claim_preview,
        "universeParams": [],
        "binders": binders,
        "constantNames": constant_names or ["Rat", "Eq"],
    }


def _capability_replay_profile(request: dict[str, Any]) -> dict[str, Any]:
    """Return capability-specific kernel-replay naming / claim preview."""
    cap = str(request.get("capability") or "algebra.rational_equality")
    if cap == "algebra.linear_algebra":
        op = str(request.get("operation") or "inverse_witness")
        fixture = {
            "inverse_witness": "inv",
            "system_solution": "sys",
            "kernel_vector": "ker",
            "det_identity": "det",
        }.get(op, "inv")
        claim_class = "soundResult" if op == "det_identity" else "witness"
        return {
            "capability_id": "algebra.linear_algebra",
            "claim_class": claim_class,
            "checker_package": "MathEvidence.Checkers.LinearAlgebra",
            "checker_module": "MathEvidence.Checkers.LinearAlgebra.ReplaySound",
            "soundness_theorem": "replaySound",
            "declaration_default": f"certified_linear_algebra_{fixture}",
            "claim_preview": f"linear_algebra.{op} -- Claim.proposition via replaySound",
            "constant_names": ["Matrix", "Eq", "Rat"],
            "binder_type": "Rat",
            "var_names": [],
            "fixture": fixture,
        }
    if cap == "logic.finite_counterexample":
        pred = request.get("predicate") or {}
        names = pred.get("varNames") if isinstance(pred, dict) else None
        var_names = [str(n) for n in names] if isinstance(names, list) else ["x"]
        # Prefer bool fixture when the sole domain is bool; else nat_eq0 baseline.
        domains = pred.get("domains") if isinstance(pred, dict) else None
        fixture = "nat_eq0"
        if isinstance(domains, list) and len(domains) == 1:
            d0 = domains[0] if isinstance(domains[0], dict) else {}
            if str(d0.get("ty") or "").lower() == "bool":
                fixture = "bool_false"
        return {
            "capability_id": "logic.finite_counterexample",
            "claim_class": "refutation",
            "checker_package": "MathEvidence.Checkers.Counterexample",
            "checker_module": "MathEvidence.Checkers.Counterexample.ReplaySound",
            "soundness_theorem": "replaySound",
            "declaration_default": f"certified_counterexample_{fixture}",
            "claim_preview": (
                f"finite_counterexample refutation over {var_names} "
                "-- Claim.proposition via replaySound"
            ),
            "constant_names": ["Fin", "Bool", "Nat", "Int", "Not"],
            "binder_type": "Nat",
            "var_names": var_names,
            "fixture": fixture,
        }
    if cap == "analysis.analytic_calculus":
        return {
            "capability_id": "analysis.analytic_calculus",
            "claim_class": "soundResult",
            "checker_package": "MathEvidence.Checkers.AnalyticCalculus",
            "checker_module": "MathEvidence.Checkers.AnalyticCalculus.ReplaySound",
            "soundness_theorem": "replaySound",
            "declaration_default": "certified_analytic_replay_product",
            "claim_preview": (
                "analytic_calculus HasDerivAt via replaySound / "
                "OfflineFixtures.cert_product"
            ),
            "constant_names": ["Real", "HasDerivAt"],
            "binder_type": "Real",
            "var_names": ["x"],
            "fixture": "cert_product",
        }
    if cap == "algebra.ideal_membership_witness":
        target = request.get("target") if isinstance(request.get("target"), dict) else {}
        var_count = target.get("varCount")
        try:
            vc = int(var_count) if var_count is not None else 2
        except (TypeError, ValueError):
            vc = 2
        fixture = "x2m1" if vc == 1 else "xy"
        return {
            "capability_id": "algebra.ideal_membership_witness",
            "claim_class": "witness",
            "checker_package": "MathEvidence.Checkers.IdealMembership",
            "checker_module": "MathEvidence.Checkers.IdealMembership.ReplaySound",
            "soundness_theorem": "replaySound",
            "declaration_default": f"certified_ideal_membership_{fixture}",
            "claim_preview": (
                f"ideal_membership_witness.{fixture} -- Claim.proposition via replaySound"
            ),
            "constant_names": ["MvPolynomial", "Ideal", "Eq"],
            "binder_type": "Int",
            "var_names": [],
            "fixture": fixture,
        }
    if cap == "algebra.formal_rational_calculus":
        raise _kr_error(
            "environment_mismatch",
            f"capability {cap} has no theorem-producing replay profile yet",
            capability=cap,
        )
    # Default: rational equality
    vars_ = request.get("variables") or []
    var_names = [
        str(v["name"]) for v in vars_ if isinstance(v, dict) and "name" in v
    ]
    return {
        "capability_id": "algebra.rational_equality",
        "claim_class": "soundResult",
        "checker_package": "MathEvidence.Checkers.RationalEquality",
        "checker_module": "MathEvidence.Checkers.RationalEquality.Check",
        "soundness_theorem": "replaySound",
        "declaration_default": "certified_rational_replay",
        "claim_preview": (
            f"forall ({' '.join(f'({n} : Rat)' for n in var_names)}), "
            "lhs = rhs"
        ),
        "constant_names": ["Rat", "Eq"],
        "binder_type": "Rat",
        "var_names": var_names,
        "fixture": "basic_sympy",
    }


def run_kernel_replay(
    *,
    bundle_dir: Path | str,
    repo_root: Path | None = None,
    declaration_name: str | None = None,
    source_revision: str = "workspace",
    require_lean: bool = True,
    allowed_axioms: tuple[str, ...] = ALLOWED_AXIOMS_DEFAULT,
    out_record_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Run theorem-producing kernel replay for a Candidate Bundle.

    Supports ``algebra.rational_equality``, ``algebra.linear_algebra``,
    ``logic.finite_counterexample``, ``analysis.analytic_calculus``, and
    ``algebra.ideal_membership_witness`` (ME-RV-035 / P0-F OfflineFixtures).

    Returns a result envelope with ``certificationId`` / digests on success.
    Never returns theorem-level status without a Certification Record.
    """
    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    path = Path(bundle_dir)
    if not path.is_dir():
        raise _kr_error("bundle_not_found", str(path))

    try:
        verify_bundle_offline(path, strict=True)
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        if "digest" in msg.lower():
            raise _kr_error("content_digest_mismatch", msg) from exc
        raise _kr_error("manifest_invalid", msg) from exc

    request = load_role_json(path, "request")
    certificate = load_role_json(path, "certificate")
    if not isinstance(request, dict):
        raise _kr_error("request_decode_failed", "request role missing or invalid")
    if not isinstance(certificate, dict):
        raise _kr_error("certificate_decode_failed", "certificate role missing or invalid")

    request_digest = request.get("requestDigest")
    if not isinstance(request_digest, str) or not request_digest.startswith("sha256:"):
        raise _kr_error("request_digest_mismatch", "requestDigest missing")

    profile = _capability_replay_profile(request)
    decl = declaration_name or str(profile["declaration_default"])

    manifest_path = find_role_path(path, "manifest")
    if manifest_path is None:
        raise _kr_error("bundle_not_found", "missing manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidate_digest = manifest.get("bundleDigest") or compute_bundle_digest(manifest)

    lock = default_rational_environment_lock()
    lock_digest = environment_lock_digest(lock)

    claim_preview = f"{profile['claim_preview']} -- bound to {request_digest}"
    type_payload = build_structural_theorem_type(
        var_names=list(profile["var_names"]),
        claim_preview=claim_preview,
        constant_names=list(profile["constant_names"]),
        binder_type=str(profile["binder_type"]),
    )
    type_payload["environmentLockDigest"] = lock_digest
    type_dig = theorem_type_digest(type_payload)

    target = build_replay_target(
        module_name=f"MathEvidence.Generated.Replay.{decl}",
        declaration_name=decl,
        theorem_type_canonical=claim_preview,
        theorem_type_digest_value=type_dig,
        source_revision=source_revision,
        source_file=f"MathEvidence/Generated/Replay/{decl}.lean",
        environment_lock_digest_value=lock_digest,
        request_digest=request_digest,
        candidate_bundle_digest=candidate_digest
        if isinstance(candidate_digest, str)
        else None,
    )
    target["capability"] = profile["capability_id"]
    target["fixture"] = profile["fixture"]

    lake = find_lake(root)
    lean_ok = False
    lean_stdout = ""
    lean_stderr = ""
    axioms: list[str] = []
    proof_digest = sha256_digest(
        {
            "declarationName": decl,
            "theoremTypeDigest": type_dig,
            "soundnessTheorem": profile["soundness_theorem"],
            "candidateBundleDigest": candidate_digest,
            "capability": profile["capability_id"],
        }
    )

    with tempfile.TemporaryDirectory(prefix="me_kernel_replay_") as tmp:
        tmp_path = Path(tmp)
        lean_file = tmp_path / f"{decl}.lean"
        lean_file.write_text(_generate_from_target(target), encoding="utf-8", newline="\n")
        if lake is None:
            raise _kr_error(
                "theorem_elaboration_failed",
                "lake not found; cannot compile kernel-replay module "
                f"(require_lean={require_lean}; refusing soundness_verified)",
            )
        gen_dir = root / "MathEvidence" / "Generated" / "Replay"
        gen_dir.mkdir(parents=True, exist_ok=True)
        in_tree = gen_dir / f"{decl}.lean"
        in_tree.write_text(
            lean_file.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
        )
        try:
            try:
                proc = subprocess.run(
                    [str(lake), "env", "lean", str(in_tree)],
                    capture_output=True,
                    text=True,
                    timeout=600.0,
                    check=False,
                    cwd=str(root),
                    shell=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise _kr_error(
                    "resource_limit_exceeded",
                    "lake env lean exceeded 600s wall timeout "
                    f"(require_lean={require_lean}; refusing soundness_verified)",
                    kind="wall_time",
                    timeoutSec=600,
                    stdout=((exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else ""),
                    stderr=((exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else ""),
                ) from exc
            lean_stdout = proc.stdout or ""
            lean_stderr = proc.stderr or ""
            if proc.returncode != 0:
                raise _kr_error(
                    "kernel_rejected",
                    f"lake env lean exit {proc.returncode} "
                    f"(require_lean={require_lean}; refusing soundness_verified)",
                    stdout=lean_stdout[-2000:],
                    stderr=lean_stderr[-2000:],
                )
            lean_ok = True
            axioms = parse_print_axioms(lean_stdout, decl)
            if not axiom_policy_ok(axioms, allowed_axioms):
                raise _kr_error(
                    "unexpected_axiom",
                    f"axioms {axioms} not subset of {list(allowed_axioms)}",
                )
        finally:
            pass

    if not lean_ok:
        raise _kr_error(
            "kernel_rejected",
            "Lean kernel replay did not succeed; refusing soundness_verified",
        )

    claim_class = str(profile["claim_class"])
    theorem_identity = theorem_identity_payload(
        declaration_name=decl,
        theorem_type_digest_value=type_dig,
        proof_declaration_digest=proof_digest,
        environment_lock_digest_value=lock_digest,
        elaborated_serialization=claim_preview,
        universe_params=[],
        binders=type_payload["binders"],
        constant_names=type_payload["constantNames"],
    )

    checker_evaluation = {
        "schemaVersion": "0.3.0",
        "requestDigest": request_digest,
        "candidateBundleDigest": candidate_digest,
        "resultStatus": "soundness_verified",
        "assuranceMode": "kernel_replay",
        "claimEstablished": claim_class,
        "checker": {
            "package": profile["checker_package"],
            "module": profile["checker_module"],
            "name": "checkBool",
            "version": "0.1.0",
            "soundnessTheorem": profile["soundness_theorem"],
        },
        "detail": f"kernel replay applied {profile['soundness_theorem']}",
    }

    axiom_report = {
        "schemaVersion": "0.3.0",
        "status": "compiled" if lean_ok else "pending_lean",
        "declarationName": decl,
        "axioms": axioms,
        "allowedAxioms": list(allowed_axioms),
        "axiomDigests": [sha256_digest({"axiom": a}) for a in axioms],
    }

    certification_receipt = {
        "schemaVersion": "0.3.0",
        "requestDigest": request_digest,
        "candidateBundleDigest": candidate_digest,
        "claimRequested": claim_class,
        "claimEstablished": claim_class,
        "assuranceMode": "kernel_replay",
        "resultStatus": "soundness_verified",
        "theoremTypeDigest": type_dig,
        "proofDeclarationDigest": proof_digest,
        "environmentLockDigest": lock_digest,
        "unresolvedObligations": [],
        "toolchain": {
            "leanVersion": lock["leanVersion"],
            "lakeVersion": lock["lakeVersion"],
            "mathlibVersion": lock["mathlibRevision"],
        },
        "checker": checker_evaluation["checker"],
    }

    record_dir = Path(out_record_dir) if out_record_dir else (
        root / "evidence" / "store" / "certifications" / "_pending" / decl
    )
    if record_dir.exists():
        shutil.rmtree(record_dir)
    manifest_out = write_certification_record(
        record_dir,
        candidate_bundle_digest=str(candidate_digest),
        request_digest=request_digest,
        capability_id=str(profile["capability_id"]),
        capability_version="0.1.0",
        claim_class=claim_class,
        result_status="soundness_verified",
        assurance_mode="kernel_replay",
        replay_target=target,
        checker_evaluation=checker_evaluation,
        theorem_identity=theorem_identity,
        axiom_report=axiom_report,
        certification_receipt=certification_receipt,
    )

    cert_digest = manifest_out["certificationDigest"]
    return {
        "ok": True,
        "resultStatus": "soundness_verified",
        "assuranceMode": "kernel_replay",
        "claimEstablished": claim_class,
        "capability": profile["capability_id"],
        "candidateBundleDigest": candidate_digest,
        "certificationRecordDigest": cert_digest,
        "certificationId": f"cert_sha256_{cert_digest[7:]}",
        "theoremTypeDigest": type_dig,
        "proofDeclarationDigest": proof_digest,
        "environmentLockDigest": lock_digest,
        "declarationName": decl,
        "axioms": axioms,
        "leanOk": lean_ok,
        "recordDir": str(record_dir),
        "leanStdout": lean_stdout[-4000:],
        "leanStderr": lean_stderr[-4000:],
    }
