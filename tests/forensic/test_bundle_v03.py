"""Wave 1 forensic tests: Candidate Bundle v0.3, store collisions, certification."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adapters.common.bundle import (
    BUNDLE_VERSION,
    compute_bundle_digest,
    file_digest,
    verify_bundle_offline,
    write_bundle,
    write_candidate_bundle,
    write_certification_record,
)
from adapters.common.canonical import bind_request_digest, sha256_digest
from agent.api.bundle_store import BundleStore, ContentAddressCollision
from agent.api.receipt import verify_certification_record

ROOT = Path(__file__).resolve().parents[2]


def _minimal_rational_request() -> dict:
    req = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [{"name": "x", "type": "Rat"}],
        "lhs": {
            "tag": "add",
            "left": {"tag": "var", "name": "x"},
            "right": {"tag": "int", "value": "0"},
        },
        "rhs": {"tag": "var", "name": "x"},
        "knownAssumptions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
    }
    return bind_request_digest(req)


def _minimal_certificate(request_digest: str, *, backend_id: str = "test") -> dict:
    return {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "requestDigest": request_digest,
        "differenceNumerator": {"tag": "int", "value": "0"},
        "denominatorFactors": [],
        "factorization": {"method": "test", "notes": "unit"},
        "provenance": {
            "backendId": backend_id,
            "backendVersion": "0",
            "adapterVersion": "0.1.0",
            "generatedAt": "2026-07-21T00:00:00Z",
            "deterministic": True,
        },
    }


def _zero_digest() -> str:
    return "sha256:" + "ab" * 32


def test_write_candidate_bundle_v03(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    out = tmp_path / "bundle"
    manifest = write_candidate_bundle(
        out,
        request=request,
        candidate={"schemaVersion": "0.1.0"},
        certificate=cert,
    )
    assert manifest["bundleVersion"] == BUNDLE_VERSION
    assert manifest["artifactKind"] == "candidate"
    assert manifest["resultStatus"] == "computed"
    assert manifest["bundleDigest"] == compute_bundle_digest(manifest)
    assert (out / "provenance.cjson").is_file()
    assert not (out / "theorem.lean").is_file()
    assert not (out / "axiom-report.cjson").is_file()
    assert not (out / "checker-receipt.cjson").is_file()
    assert not (out / "request.json").is_file()
    warnings = verify_bundle_offline(out, strict=True)
    assert isinstance(warnings, list)


def test_candidate_rejects_verified_status(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    manifest = write_bundle(
        tmp_path / "b",
        request=request,
        candidate={},
        certificate=cert,
        result_status="soundness_verified",
    )
    assert manifest["resultStatus"] == "computed"


def test_duplicate_role_rejects(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    out = tmp_path / "dup"
    write_candidate_bundle(out, request=request, candidate={}, certificate=cert)
    shutil.copy(out / "request.cjson", out / "request-copy.cjson")
    manifest = json.loads((out / "manifest.cjson").read_text(encoding="utf-8"))
    manifest["files"].append(
        {
            "path": "request-copy.cjson",
            "digest": file_digest(out / "request-copy.cjson"),
            "mediaType": "application/cjson",
            "role": "request",
        }
    )
    manifest["bundleDigest"] = compute_bundle_digest(manifest)
    from adapters.common.bundle import write_cjson

    write_cjson(out / "manifest.cjson", manifest)
    with pytest.raises(ValueError, match="duplicate"):
        verify_bundle_offline(out, strict=True)


def test_extra_unlisted_file_rejects(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cert = _minimal_certificate(request["requestDigest"])
    out = tmp_path / "extra"
    write_candidate_bundle(out, request=request, candidate={}, certificate=cert)
    (out / "evil.txt").write_text("nope\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unlisted"):
        verify_bundle_offline(out, strict=True)


def test_same_request_different_backends_distinct_digests(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    a = write_candidate_bundle(
        tmp_path / "a",
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"], backend_id="sympy"),
    )
    b = write_candidate_bundle(
        tmp_path / "b",
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"], backend_id="sage"),
    )
    assert a["requestDigest"] == b["requestDigest"]
    assert a["bundleDigest"] != b["bundleDigest"]


def test_content_store_idempotent_recommit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "evidence" / "store").mkdir(parents=True)
    (repo / "agent" / "store").mkdir(parents=True)
    request = _minimal_rational_request()
    bundle = tmp_path / "src"
    manifest = write_candidate_bundle(
        bundle,
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"]),
    )
    store = BundleStore.default(repo)
    p1, id1 = store.commit_content_addressed(
        bundle,
        request_digest=manifest["requestDigest"],
        bundle_digest=manifest["bundleDigest"],
    )
    p2, id2 = store.commit_content_addressed(
        bundle,
        request_digest=manifest["requestDigest"],
        bundle_digest=manifest["bundleDigest"],
    )
    assert p1 == p2
    assert id1 == id2
    assert id1.startswith("sha256_")
    index = store.read_request_index(manifest["requestDigest"])
    assert manifest["bundleDigest"] in index


def test_content_store_collision_rejects(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "evidence" / "store").mkdir(parents=True)
    (repo / "agent" / "store").mkdir(parents=True)
    request = _minimal_rational_request()
    bundle = tmp_path / "src"
    manifest = write_candidate_bundle(
        bundle,
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"]),
    )
    store = BundleStore.default(repo)
    store.commit_content_addressed(
        bundle,
        request_digest=manifest["requestDigest"],
        bundle_digest=manifest["bundleDigest"],
    )
    clone = tmp_path / "clone"
    shutil.copytree(bundle, clone)
    (clone / "README.md").write_text("# tampered\n", encoding="utf-8")
    with pytest.raises(ContentAddressCollision):
        store.commit_content_addressed(
            clone,
            request_digest=manifest["requestDigest"],
            bundle_digest=manifest["bundleDigest"],
            verify=False,
        )


def test_certification_receipt_coherence_native_checked(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cand = tmp_path / "cand"
    cand_manifest = write_candidate_bundle(
        cand,
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"]),
    )
    digest = _zero_digest()
    receipt = {
        "schemaVersion": "0.3.0",
        "candidateBundleDigest": cand_manifest["bundleDigest"],
        "certificationRecordDigest": digest,
        "requestDigest": request["requestDigest"],
        "certificateContentDigest": digest,
        "replayTargetDigest": digest,
        "theoremTypeDigest": digest,
        "proofDeclarationDigest": digest,
        "axiomReportDigest": digest,
        "environmentLockDigest": digest,
        "capability": {"id": "algebra.rational_equality", "version": "0.1.0"},
        "checker": {
            "package": "MathEvidence.Checkers.RationalEquality",
            "module": "Check",
            "name": "checkBool",
            "version": "0.1.0",
        },
        "claimRequested": "soundResult",
        "claimEstablished": "soundResult",
        "unresolvedObligations": [],
        "assuranceMode": "native_checked",
        "resultStatus": "soundness_verified",
        "toolchain": {"leanVersion": "4.14.0", "lakeVersion": "lake"},
    }
    with pytest.raises(ValueError, match="native_checked"):
        write_certification_record(
            tmp_path / "cert",
            candidate_bundle_digest=cand_manifest["bundleDigest"],
            request_digest=request["requestDigest"],
            capability_id="algebra.rational_equality",
            capability_version="0.1.0",
            claim_class="soundResult",
            result_status="soundness_verified",
            assurance_mode="native_checked",
            replay_target={"schemaVersion": "0.3.0", "detail": "stub"},
            checker_evaluation={
                "schemaVersion": "0.3.0",
                "resultStatus": "checker_accepted",
            },
            theorem_identity={
                "schemaVersion": "0.3.0",
                "theoremTypeDigest": digest,
                "proofDeclarationDigest": digest,
                "environmentLockDigest": digest,
            },
            axiom_report={
                "schemaVersion": "0.3.0",
                "status": "compiled",
                "axiomDigests": [],
            },
            certification_receipt=receipt,
        )


def test_rational_theorem_certification_is_rejected_even_when_structurally_coherent(
    tmp_path: Path,
) -> None:
    from adapters.common.theorem_identity import (
        build_replay_target,
        default_rational_environment_lock,
        environment_lock_digest,
    )

    request = _minimal_rational_request()
    cand = tmp_path / "cand"
    cand_manifest = write_candidate_bundle(
        cand,
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"]),
    )
    d = sha256_digest({"k": "v"})
    lock = environment_lock_digest(default_rational_environment_lock())
    declaration = "forensic_rational_structural_only"
    cert_path = next(
        e["digest"] for e in cand_manifest["files"] if e["path"] == "certificate.cjson"
    )
    receipt = {
        "schemaVersion": "0.3.0",
        "candidateBundleDigest": cand_manifest["bundleDigest"],
        "certificationRecordDigest": d,
        "requestDigest": request["requestDigest"],
        "certificateContentDigest": cert_path,
        "replayTargetDigest": d,
        "theoremTypeDigest": d,
        "proofDeclarationDigest": d,
        "axiomReportDigest": d,
        "environmentLockDigest": lock,
        "capability": {"id": "algebra.rational_equality", "version": "0.1.0"},
        "checker": {
            "package": "MathEvidence.Checkers.RationalEquality",
            "module": "Check",
            "name": "checkBool",
            "version": "0.1.0",
            "soundnessTheorem": "checkBool_sound",
        },
        "soundnessTheorem": "checkBool_sound",
        "claimRequested": "soundResult",
        "claimEstablished": "soundResult",
        "unresolvedObligations": [],
        "assuranceMode": "kernel_replay",
        "resultStatus": "soundness_verified",
        "toolchain": {"leanVersion": "4.14.0", "lakeVersion": "lake"},
    }
    cert_dir = tmp_path / "cert"
    write_certification_record(
        cert_dir,
        candidate_bundle_digest=cand_manifest["bundleDigest"],
        request_digest=request["requestDigest"],
        capability_id="algebra.rational_equality",
        capability_version="0.1.0",
        claim_class="soundResult",
        result_status="soundness_verified",
        assurance_mode="kernel_replay",
        replay_target=build_replay_target(
            module_name="MathEvidence.Generated.Replay.forensic_rational_structural_only",
            declaration_name=declaration,
            theorem_type_canonical="forensic-rational-structural-only",
            theorem_type_digest_value=d,
            source_revision="historical-structural-fixture",
            source_file="MathEvidence/Generated/Replay/forensic_rational_structural_only.lean",
            environment_lock_digest_value=lock,
            request_digest=request["requestDigest"],
            capability_id="algebra.rational_equality",
            capability_version="0.1.0",
            candidate_bundle_digest=cand_manifest["bundleDigest"],
        ),
        checker_evaluation={
            "schemaVersion": "0.3.0",
            "resultStatus": "checker_accepted",
            "assuranceMode": "native_checked",
        },
        theorem_identity={
            "schemaVersion": "0.3.0",
            "serializerVersion": "mathevidence-theorem-identity-0.3",
            "declarationName": declaration,
            "theoremTypeDigest": d,
            "proofDeclarationDigest": d,
            "environmentLockDigest": lock,
        },
        axiom_report={
            "schemaVersion": "0.3.0",
            "status": "compiled",
            "axiomDigests": [],
            "allowedAxioms": ["propext"],
        },
        certification_receipt=receipt,
    )
    with pytest.raises(ValueError, match="allowedOutcomes"):
        verify_certification_record(cert_dir, candidate_dir=cand)


def test_migration_script_deterministic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two dry-run migrations over the same tree produce identical reports."""
    import scripts.migrate_bundles_v03 as mig

    request = _minimal_rational_request()
    src = tmp_path / "evidence" / "examples" / "sample"
    write_candidate_bundle(
        src,
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"]),
    )
    monkeypatch.setattr(mig, "ROOT", tmp_path)
    monkeypatch.setattr(mig, "collect_targets", lambda: [src])
    r1 = mig.migrate_one(src, dry_run=True)
    r2 = mig.migrate_one(src, dry_run=True)
    assert r1 == r2
