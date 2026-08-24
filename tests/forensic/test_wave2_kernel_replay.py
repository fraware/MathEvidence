"""Wave 2 kernel replay positive/negative and overclaim forensic tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adapters.common.bundle import (
    verify_bundle_offline,
    write_candidate_bundle,
)
from adapters.common.canonical import bind_request_digest
from adapters.common.kernel_replay import (
    KERNEL_REPLAY_CODES,
    KernelReplayError,
    axiom_policy_ok,
    find_lake,
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


def _ideal_poly(m: int, coefficient: int, exponents: list[int]) -> dict:
    return {
        "varCount": m,
        "terms": [{"coefficient": coefficient, "exponents": exponents}],
    }


def _write_exact_ideal_bundle(bundle: Path) -> None:
    target = _ideal_poly(2, 1, [1, 1])
    generators = [_ideal_poly(2, 1, [1, 0]), _ideal_poly(2, 1, [0, 1])]
    request = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.ideal_membership_witness",
            "capabilityVersion": "0.1.0",
            "target": target,
            "generators": generators,
            "requestedClaim": "witness",
        }
    )
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": "0.1.0",
        "requestDigest": request["requestDigest"],
        "target": target,
        "generators": generators,
        "multipliers": [
            _ideal_poly(2, 1, [0, 1]),
            {"varCount": 2, "terms": []},
        ],
        "claimClass": "witness",
        "pythonMirrorAccepts": True,
        "provenance": {
            "adapterVersion": "forensic",
            "backendId": "forensic_exact_witness",
            "backendVersion": "test",
            "deterministic": True,
            "generatedAt": "forensic-test",
        },
    }
    candidate = {
        "reportedOk": True,
        "multipliers": certificate["multipliers"],
        "backend": "forensic_exact_witness",
    }
    write_candidate_bundle(
        bundle,
        request=request,
        candidate=candidate,
        certificate=certificate,
        claim_class="candidate",
        assurance_mode="native_checked",
    )


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


def test_generic_rational_replay_fails_closed(tmp_path: Path) -> None:
    """OfflineFixtures are no longer generic Certification Record authority."""
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
    with pytest.raises(KernelReplayError) as exc:
        run_kernel_replay(
            bundle_dir=bundle,
            repo_root=ROOT,
            declaration_name="forensic_rational_must_not_certify",
            require_lean=False,
            out_record_dir=tmp_path / "cert_record",
        )
    assert "assurance_mode_unavailable" in str(exc.value)
    assert not (tmp_path / "cert_record" / "manifest.cjson").is_file()


@pytest.mark.skipif(
    find_lake(ROOT) is None,
    reason="lake unavailable; exact theorem-producing replay requires Lean",
)
def test_exact_ideal_kernel_replay_uses_lean_declaration_identity(tmp_path: Path) -> None:
    bundle = tmp_path / "candidate"
    _write_exact_ideal_bundle(bundle)
    out = tmp_path / "cert_record"
    result = run_kernel_replay(
        bundle_dir=bundle,
        repo_root=ROOT,
        declaration_name="forensic_exact_ideal",
        require_lean=True,
        out_record_dir=out,
    )
    assert result["ok"] is True
    assert result["resultStatus"] == "soundness_verified"
    assert result["claimEstablished"] == "witness"
    assert result["identityAuthority"] == "Lean.Environment ConstantInfo"
    assert result["leanOk"] is True
    assert result["theoremTypeDigest"].startswith("sha256:")
    assert result["proofDeclarationDigest"].startswith("sha256:")
    verify_bundle_offline(out, strict=True)
    theorem_identity = json.loads(
        (out / "theorem-identity.cjson").read_text(encoding="utf-8")
    )
    assert theorem_identity["theoremTypeDigest"] == result["theoremTypeDigest"]
    assert theorem_identity["proofDeclarationDigest"] == result["proofDeclarationDigest"]
    assert "OfflineFixtures" not in (
        ROOT
        / "MathEvidence"
        / "Generated"
        / "Replay"
        / "forensic_exact_ideal.lean"
    ).read_text(encoding="utf-8")


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
