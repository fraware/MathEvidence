"""Wave 2 kernel replay positive/negative and overclaim forensic tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adapters.common.bundle import write_candidate_bundle, write_certification_record
from adapters.common.kernel_replay import (
    KERNEL_REPLAY_CODES,
    axiom_policy_ok,
    parse_print_axioms,
    run_kernel_replay,
)
from adapters.common.theorem_identity import default_rational_environment_lock
from agent.api import service
from studio.epistemic_contract import (
    certification_gate,
    epistemic_from_result_status,
    verify_checker_receipt,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "evidence" / "examples" / "rational_equality_basic"


def _load_example_roles() -> tuple[dict, dict, dict]:
    req = json.loads((EXAMPLE / "request.cjson").read_text(encoding="utf-8"))
    cand = json.loads((EXAMPLE / "candidate.cjson").read_text(encoding="utf-8"))
    cert = json.loads((EXAMPLE / "certificate.cjson").read_text(encoding="utf-8"))
    return req, cand, cert


def test_kernel_replay_error_codes_documented() -> None:
    required = {
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
        "replay_dependency_missing",
        "assurance_mode_unavailable",
    }
    assert required <= KERNEL_REPLAY_CODES


def test_axiom_policy_rejects_unexpected() -> None:
    assert axiom_policy_ok(["propext"])
    assert not axiom_policy_ok(["propext", "evil_axiom"])


def test_parse_print_axioms() -> None:
    out = "'certified' depends on axioms: [propext, Quot.sound]\n"
    assert parse_print_axioms(out, "certified") == ["propext", "Quot.sound"]


def test_kernel_replay_missing_bundle(tmp_path: Path) -> None:
    with pytest.raises(Exception) as exc:
        run_kernel_replay(
            bundle_dir=tmp_path / "missing",
            repo_root=ROOT,
            require_lean=False,
        )
    assert "bundle_not_found" in str(exc.value).lower() or "bundle" in str(exc.value).lower()


def test_kernel_replay_positive_without_lean(tmp_path: Path) -> None:
    """Without Lean success, MUST NOT emit soundness_verified (ME-RV-022)."""
    req, cand, cert = _load_example_roles()
    bundle = tmp_path / "candidate"
    write_candidate_bundle(
        bundle,
        request=req,
        candidate=cand,
        certificate=cert,
        claim_class="soundResult",
        assurance_mode="native_checked",
    )
    out = tmp_path / "cert_record"
    # Force the no-lake path by monkeypatching find_lake when needed is heavy;
    # require_lean=False must still refuse Certified if compile fails / lake missing.
    # If lake is present and Mathlib builds the generated module, success is OK.
    try:
        result = run_kernel_replay(
            bundle_dir=bundle,
            repo_root=ROOT,
            declaration_name="forensic_positive",
            require_lean=False,
            out_record_dir=out,
        )
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        assert any(
            k in msg
            for k in (
                "theorem_elaboration",
                "kernel_rejected",
                "lake not found",
                "refusing soundness_verified",
            )
        ), msg
        assert not (out / "manifest.cjson").is_file()
        return
    assert result["ok"] is True
    assert result["resultStatus"] == "soundness_verified"
    assert result.get("leanOk") is True
    assert (out / "manifest.cjson").is_file()
    assert (out / "replay-target.cjson").is_file()
    assert (out / "theorem-identity.cjson").is_file()
    assert (out / "axiom-report.cjson").is_file()
    # Candidate bundle must not be mutated with certification roles.
    assert not (bundle / "theorem-identity.cjson").exists()
    assert not (bundle / "certification-receipt.cjson").exists()
    axiom = json.loads((out / "axiom-report.cjson").read_text(encoding="utf-8"))
    assert axiom.get("status") == "compiled"

def test_kernel_replay_negative_tampered_certificate(tmp_path: Path) -> None:
    req, cand, cert = _load_example_roles()
    bundle = tmp_path / "candidate"
    write_candidate_bundle(
        bundle,
        request=req,
        candidate=cand,
        certificate=cert,
        claim_class="soundResult",
        assurance_mode="native_checked",
    )
    # Tamper certificate bytes after manifest binding.
    cert_path = bundle / "certificate.cjson"
    data = json.loads(cert_path.read_text(encoding="utf-8"))
    data["denomFactors"] = data.get("denomFactors") or []
    data["denomFactors"] = list(data["denomFactors"]) + [
        {"tag": "int", "value": "999"}
    ]
    cert_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(Exception) as exc:
        run_kernel_replay(
            bundle_dir=bundle,
            repo_root=ROOT,
            require_lean=False,
            out_record_dir=tmp_path / "cert",
        )
    msg = str(exc.value).lower()
    assert "digest" in msg or "manifest" in msg or "content" in msg


def test_studio_never_certifies_raw_receipt() -> None:
    receipt = {
        "requestDigest": "sha256:" + ("a" * 64),
        "resultStatus": "soundness_verified",
        "claimEstablished": "soundResult",
        "assuranceMode": "kernel_replay",
        "theoremDigest": "sha256:" + ("b" * 64),
    }
    gate = verify_checker_receipt(receipt)
    assert gate["allowCertified"] is False


def test_studio_certifies_only_with_agent_certification_fields() -> None:
    denied = certification_gate(
        certification_verified=False,
        certification_id="cert_sha256_" + ("c" * 64),
        claim_established="soundResult",
        theorem_type_digest="sha256:" + ("d" * 64),
        result_status="soundness_verified",
    )
    assert denied["allowCertified"] is False

    allowed = certification_gate(
        certification_verified=True,
        certification_id="cert_sha256_" + ("c" * 64),
        claim_established="soundResult",
        theorem_type_digest="sha256:" + ("d" * 64),
        result_status="soundness_verified",
    )
    assert allowed["allowCertified"] is True

    # leanStatus alone never Certified.
    epi = epistemic_from_result_status(
        "soundness_verified", lean_status="soundness_verified"
    )
    assert epi["allowCertified"] is False


def test_agent_verify_bundle_never_theorem_status(tmp_path: Path) -> None:
    req, cand, cert = _load_example_roles()
    bundle = tmp_path / "cand"
    write_candidate_bundle(
        bundle,
        request=req,
        candidate=cand,
        certificate=cert,
        claim_class="soundResult",
        assurance_mode="native_checked",
    )
    store = ROOT / "agent" / "store" / "bundles" / "wave2_verify_forensic"
    if store.exists():
        shutil.rmtree(store)
    shutil.copytree(bundle, store)
    try:
        out = service.op_verify_bundle({"bundleId": "wave2_verify_forensic"})
        assert out["resultStatus"] not in {
            "soundness_verified",
            "witness_verified",
            "completeness_verified",
            "optimality_verified",
            "native_verified",
        }
        assert out.get("certificationVerified") is False
        assert out.get("claimEstablished") in (None, False)
    finally:
        if store.exists():
            shutil.rmtree(store)


def test_registry_rational_protocol_reference() -> None:
    cap = json.loads(
        (
            ROOT / "registry" / "capabilities" / "algebra.rational_equality.json"
        ).read_text(encoding="utf-8")
    )
    assert cap["role"] == "protocol_reference"
    assert cap["externalSearchEssential"] is False


def test_environment_lock_default_stable() -> None:
    lock = default_rational_environment_lock()
    assert lock["leanVersion"] == "leanprover/lean4:v4.14.0"
    assert "MathEvidence.Checkers.RationalEquality.Check" in lock["imports"]
