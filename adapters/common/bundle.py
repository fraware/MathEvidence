"""Evidence bundle helpers (Python orchestration; Lean checker is separate).

Evidence Bundle **v0.3** splits Candidate Bundles from Certification Records.

Candidate Bundle (status ``computed``):
  request, candidate, certificate, provenance, manifest — no theorem/receipt/axiom.

Certification Record (separate directory):
  replay-target, checker-evaluation, theorem-identity, axiom-report,
  certification-receipt, optional signature, manifest.

``bundleDigest = SHA256(JCS(manifestBindingPayload))`` over roles/content digests;
never the request digest alone.

Legacy v0.1/v0.2 trees remain readable via dual-path verify.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adapters.common.canonical import canonical_dumps, sha256_digest, sha256_hex
from adapters.common.schema_validate import SchemaStore

BUNDLE_VERSION = "0.3.0"
BUNDLE_VERSION_V02 = "0.2.0"
BUNDLE_VERSION_LEGACY = "0.1.0"

PLACEHOLDER_THEOREM_NAME = "mathevidence_bundle_theorem_placeholder"
PLACEHOLDER_AXIOM_STATUS = "pending_compiled_audit"

CANDIDATE_MANDATORY_ROLES = ("request", "candidate", "certificate", "provenance")
CERTIFICATION_MANDATORY_ROLES = (
    "replay-target",
    "checker-evaluation",
    "theorem-identity",
    "axiom-report",
    "certification-receipt",
)

VERIFIED_RESULT_STATUSES = frozenset(
    {
        "witness_verified",
        "soundness_verified",
        "completeness_verified",
        "optimality_verified",
        "native_verified",
    }
)

# Role stem → wire role name
_PATH_ROLE: dict[str, str] = {
    "request": "request",
    "candidate": "candidate",
    "certificate": "certificate",
    "provenance": "provenance",
    "replay-target": "replay-target",
    "checker-evaluation": "checker-evaluation",
    "theorem-identity": "theorem-identity",
    "axiom-report": "axiom-report",
    "certification-receipt": "certification-receipt",
    "signature": "signature",
    "README": "readme",
    "readme": "readme",
    "theorem": "theorem-identity",
    "checker-receipt": "checker-evaluation",
}


def file_digest(path: Path) -> str:
    data = path.read_bytes()
    return "sha256:" + sha256_hex(data)


def write_text_lf(path: Path, text: str) -> None:
    """Write UTF-8 text with LF newlines only (platform-stable content digests)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(normalized.encode("utf-8"))


def write_json(path: Path, obj: Any) -> None:
    """Pretty JSON for non-binding / human renderings only."""
    write_text_lf(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def write_cjson(path: Path, obj: Any) -> None:
    """Canonical JSON bytes (mathevidence-jcs-0.2) for theorem-binding files."""
    write_text_lf(path, canonical_dumps(obj))


def role_from_path(rel: str) -> str:
    """Infer role wire name from a relative path."""
    name = Path(rel.replace("\\", "/")).name
    for suffix in (".cjson", ".json", ".lean", ".md"):
        if name.endswith(suffix):
            stem = name[: -len(suffix)]
            break
    else:
        stem = name
    return _PATH_ROLE.get(stem, "other")


def find_role_path(bundle_dir: Path, stem: str) -> Path | None:
    """Prefer v0.3/v0.2 ``.cjson`` then legacy ``.json`` for a bundle role stem."""
    cjson = bundle_dir / f"{stem}.cjson"
    if cjson.is_file():
        return cjson
    json_path = bundle_dir / f"{stem}.json"
    if json_path.is_file():
        return json_path
    return None


def load_role_json(bundle_dir: Path, stem: str) -> dict[str, Any]:
    path = find_role_path(bundle_dir, stem)
    if path is None:
        raise FileNotFoundError(f"missing bundle role {stem}.cjson/{stem}.json under {bundle_dir}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return data


def iter_bundle_dirs(root: Path) -> list[Path]:
    """Unique bundle directories under ``root`` that have a manifest role."""
    if not root.is_dir():
        return []
    seen: set[Path] = set()
    bundles: list[Path] = []
    for pattern in ("manifest.cjson", "manifest.json"):
        for path in root.rglob(pattern):
            parent = path.parent.resolve()
            if parent in seen:
                continue
            if find_role_path(parent, "manifest") is None:
                continue
            seen.add(parent)
            bundles.append(parent)
    return sorted(bundles)


def _media_type_for(name: str) -> str:
    if name.endswith(".md"):
        return "text/markdown"
    if name.endswith(".lean"):
        return "text/x-lean"
    if name.endswith(".cjson"):
        return "application/cjson"
    return "application/json"


def _file_entries(bundle_dir: Path, relative_files: list[str]) -> list[dict[str, str]]:
    files_meta: list[dict[str, str]] = []
    for name in relative_files:
        path = bundle_dir / name
        files_meta.append(
            {
                "path": name,
                "digest": file_digest(path),
                "mediaType": _media_type_for(name),
                "role": role_from_path(name),
            }
        )
    return files_meta


def manifest_binding_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    """Fields that participate in ``bundleDigest`` (excludes digest itself)."""
    files = manifest.get("files") or []
    roles = sorted(
        [
            {
                "role": e.get("role") or role_from_path(str(e.get("path", ""))),
                "path": e["path"],
                "mediaType": e["mediaType"],
                "digest": e["digest"],
            }
            for e in files
            if isinstance(e, dict)
        ],
        key=lambda r: (str(r["role"]), str(r["path"])),
    )
    cap = manifest.get("capability") or {}
    prov = manifest.get("provenance") or {}
    backend = prov.get("backend")
    backend_digest = sha256_digest(backend) if backend is not None else None
    resource = manifest.get("resourcePolicyDigest")
    return {
        "schemaVersion": manifest.get("bundleVersion") or manifest.get("schemaVersion"),
        "capability": {"id": cap.get("id"), "version": cap.get("version")},
        "requestDigest": manifest.get("requestDigest"),
        "claimRequested": manifest.get("claimClass"),
        "roles": roles,
        "backendProvenanceDigest": backend_digest,
        "resourcePolicyDigest": resource if isinstance(resource, str) else None,
        "artifactKind": manifest.get("artifactKind", "candidate"),
    }


def compute_bundle_digest(manifest: dict[str, Any]) -> str:
    """``bundleDigest = SHA256(JCS(manifestBindingPayload))``."""
    return sha256_digest(manifest_binding_payload(manifest))


def build_manifest(
    *,
    capability_id: str,
    capability_version: str,
    request_digest: str,
    claim_class: str,
    result_status: str,
    assurance_mode: str,
    files: list[dict[str, str]],
    provenance: dict[str, Any],
    bundle_version: str = BUNDLE_VERSION,
    artifact_kind: str = "candidate",
    bundle_digest: str | None = None,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "bundleVersion": bundle_version,
        "artifactKind": artifact_kind,
        "capability": {"id": capability_id, "version": capability_version},
        "requestDigest": request_digest,
        "claimClass": claim_class,
        "resultStatus": result_status,
        "assuranceMode": assurance_mode,
        "files": files,
        "provenance": provenance,
    }
    digest = bundle_digest if bundle_digest is not None else compute_bundle_digest(manifest)
    manifest["bundleDigest"] = digest
    return manifest


def _reject_placeholder_theorem(theorem_lean: str) -> None:
    if PLACEHOLDER_THEOREM_NAME in theorem_lean:
        raise ValueError(
            f"placeholder theorem rejected: {PLACEHOLDER_THEOREM_NAME} is not allowed"
        )


def _reject_placeholder_axiom(axiom_report: dict[str, Any]) -> None:
    status = axiom_report.get("status")
    if status == PLACEHOLDER_AXIOM_STATUS:
        raise ValueError(
            f"placeholder axiom report rejected: status={PLACEHOLDER_AXIOM_STATUS}"
        )


def _reject_duplicate_roles(files: list[dict[str, str]]) -> None:
    seen: set[str] = set()
    for entry in files:
        role = entry.get("role") or role_from_path(entry.get("path", ""))
        if role in {"other", "readme", "signature"}:
            continue
        if role in seen:
            raise ValueError(f"duplicate bundle role: {role}")
        seen.add(role)


def write_candidate_bundle(
    bundle_dir: Path,
    *,
    request: dict[str, Any],
    candidate: dict[str, Any],
    certificate: dict[str, Any],
    claim_class: str = "candidate",
    assurance_mode: str = "native_checked",
    lean_version: str = "4.x-pending",
    library_revision: str = "workspace",
    checker_version: str = "0.1.0",
    readme: str | None = None,
    schemas: SchemaStore | None = None,
    extra_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write a Candidate Bundle v0.3 directory and return the manifest.

    Always status ``computed``. Never writes theorem, axiom, or receipt roles.
    """
    store = schemas or SchemaStore()
    cap = request.get("capability")
    req_schema, cert_schema = _schemas_for_capability(cap if isinstance(cap, str) else "")
    store.validate(req_schema, request)
    store.validate(cert_schema, certificate)

    if claim_class in VERIFIED_RESULT_STATUSES:
        claim_class = "candidate"

    provenance_obj: dict[str, Any] = {
        "leanVersion": lean_version,
        "libraryRevision": library_revision,
        "checkerVersion": checker_version,
        "backend": certificate.get("provenance"),
    }
    if extra_provenance:
        provenance_obj.update(extra_provenance)

    bundle_dir.mkdir(parents=True, exist_ok=True)
    # Remove legacy dual-format leftovers that would violate strict closure.
    for stem in (
        "request",
        "candidate",
        "certificate",
        "manifest",
        "provenance",
        "checker-receipt",
        "axiom-report",
    ):
        legacy = bundle_dir / f"{stem}.json"
        if legacy.is_file():
            legacy.unlink()
    for name in ("theorem.lean", "axiom-report.cjson", "checker-receipt.cjson"):
        stale = bundle_dir / name
        if stale.is_file():
            stale.unlink()

    write_cjson(bundle_dir / "request.cjson", request)
    write_cjson(bundle_dir / "candidate.cjson", candidate)
    write_cjson(bundle_dir / "certificate.cjson", certificate)
    write_cjson(bundle_dir / "provenance.cjson", provenance_obj)

    if readme is None:
        readme = (
            f"# Candidate Bundle (v0.3)\n\n"
            f"Untrusted adapter output for `{cap}`.\n"
            "Status is always `computed`. Verification requires a separate "
            "Certification Record from kernel replay.\n"
        )
    write_text_lf(bundle_dir / "README.md", readme)

    relative_files = [
        "request.cjson",
        "candidate.cjson",
        "certificate.cjson",
        "provenance.cjson",
        "README.md",
    ]
    files_meta = _file_entries(bundle_dir, relative_files)
    _reject_duplicate_roles(files_meta)

    # Candidate packaging never claims kernel_replay / verified.
    if assurance_mode == "kernel_replay":
        assurance_mode = "native_checked"

    manifest = build_manifest(
        capability_id=request["capability"],
        capability_version=request["capabilityVersion"],
        request_digest=request["requestDigest"],
        claim_class=claim_class,
        result_status="computed",
        assurance_mode=assurance_mode,
        files=files_meta,
        provenance=provenance_obj,
        bundle_version=BUNDLE_VERSION,
        artifact_kind="candidate",
    )
    store.validate("evidence-bundle.schema.json", manifest)
    write_cjson(bundle_dir / "manifest.cjson", manifest)
    return manifest


def write_bundle(
    bundle_dir: Path,
    *,
    request: dict[str, Any],
    candidate: dict[str, Any],
    certificate: dict[str, Any],
    result_status: str = "computed",
    claim_class: str = "candidate",
    assurance_mode: str = "native_checked",
    lean_version: str = "4.x-pending",
    library_revision: str = "workspace",
    checker_version: str = "0.1.0",
    readme: str | None = None,
    schemas: SchemaStore | None = None,
    checker_receipt: dict[str, Any] | None = None,
    axiom_report: dict[str, Any] | None = None,
    theorem_lean: str | None = None,
) -> dict[str, Any]:
    """Write a Candidate Bundle v0.3 (compat wrapper).

    Theorem/axiom/receipt kwargs are rejected for Candidate Bundles — those
    belong in a Certification Record (use ``write_certification_record``).
    ``result_status`` is always coerced to ``computed``.
    """
    del result_status  # Candidate Bundles are always computed.
    if theorem_lean is not None:
        _reject_placeholder_theorem(theorem_lean)
        raise ValueError(
            "Candidate Bundle v0.3 cannot include theorem.lean; "
            "emit a Certification Record instead"
        )
    if axiom_report is not None:
        _reject_placeholder_axiom(axiom_report)
        raise ValueError(
            "Candidate Bundle v0.3 cannot include axiom-report; "
            "emit a Certification Record instead"
        )
    if checker_receipt is not None:
        raise ValueError(
            "Candidate Bundle v0.3 cannot include checker-receipt; "
            "emit a Certification Record instead"
        )
    return write_candidate_bundle(
        bundle_dir,
        request=request,
        candidate=candidate,
        certificate=certificate,
        claim_class=claim_class,
        assurance_mode=assurance_mode,
        lean_version=lean_version,
        library_revision=library_revision,
        checker_version=checker_version,
        readme=readme,
        schemas=schemas,
    )


def write_certification_record(
    record_dir: Path,
    *,
    candidate_bundle_digest: str,
    request_digest: str,
    capability_id: str,
    capability_version: str,
    claim_class: str,
    result_status: str,
    assurance_mode: str,
    replay_target: dict[str, Any],
    checker_evaluation: dict[str, Any],
    theorem_identity: dict[str, Any],
    axiom_report: dict[str, Any],
    certification_receipt: dict[str, Any],
    signature: dict[str, Any] | None = None,
    schemas: SchemaStore | None = None,
) -> dict[str, Any]:
    """Write a Certification Record v0.3 directory and return its manifest.

    Requires real theorem identity and axiom report (no placeholders).
    Replay-target stubs are allowed until Wave 2 elaborates theorem identity.
    """
    store = schemas or SchemaStore()
    _reject_placeholder_axiom(axiom_report)
    theorem_src = theorem_identity.get("source") or theorem_identity.get("leanSource")
    if isinstance(theorem_src, str):
        _reject_placeholder_theorem(theorem_src)

    if assurance_mode == "native_checked" and result_status in VERIFIED_RESULT_STATUSES:
        raise ValueError(
            "native_checked must not report theorem-level verified resultStatus"
        )
    if assurance_mode == "kernel_replay":
        for key in ("theoremTypeDigest", "proofDeclarationDigest"):
            dig = theorem_identity.get(key) or certification_receipt.get(key)
            if not isinstance(dig, str) or not dig.startswith("sha256:"):
                raise ValueError(f"kernel_replay requires {key}")

    if result_status in VERIFIED_RESULT_STATUSES:
        if certification_receipt.get("claimEstablished") in (None, "", False):
            raise ValueError("verified certification requires claimEstablished")
        if certification_receipt.get("unresolvedObligations"):
            raise ValueError("verified certification forbids unresolved obligations")

    record_dir.mkdir(parents=True, exist_ok=True)
    write_cjson(record_dir / "replay-target.cjson", replay_target)
    write_cjson(record_dir / "checker-evaluation.cjson", checker_evaluation)
    write_cjson(record_dir / "theorem-identity.cjson", theorem_identity)
    write_cjson(record_dir / "axiom-report.cjson", axiom_report)
    if signature is not None:
        write_cjson(record_dir / "signature.cjson", signature)

    receipt = dict(certification_receipt)
    receipt["schemaVersion"] = BUNDLE_VERSION
    receipt["candidateBundleDigest"] = candidate_bundle_digest
    receipt["requestDigest"] = request_digest
    receipt["replayTargetDigest"] = file_digest(record_dir / "replay-target.cjson")
    receipt["axiomReportDigest"] = file_digest(record_dir / "axiom-report.cjson")
    receipt["theoremTypeDigest"] = theorem_identity.get(
        "theoremTypeDigest", receipt.get("theoremTypeDigest")
    )
    receipt["proofDeclarationDigest"] = theorem_identity.get(
        "proofDeclarationDigest", receipt.get("proofDeclarationDigest")
    )
    receipt["environmentLockDigest"] = theorem_identity.get(
        "environmentLockDigest", receipt.get("environmentLockDigest")
    )
    receipt["assuranceMode"] = assurance_mode
    receipt["resultStatus"] = result_status

    # Certification digest binds receipt payload excluding self-digest field
    # (avoids circular dependency).
    receipt_for_binding = {
        k: v for k, v in receipt.items() if k != "certificationRecordDigest"
    }
    receipt_binding_digest = sha256_digest(receipt_for_binding)
    binding = {
        "schemaVersion": BUNDLE_VERSION,
        "candidateBundleDigest": candidate_bundle_digest,
        "replayTargetDigest": file_digest(record_dir / "replay-target.cjson"),
        "checkerEvaluationDigest": file_digest(record_dir / "checker-evaluation.cjson"),
        "theoremIdentityDigest": file_digest(record_dir / "theorem-identity.cjson"),
        "axiomReportDigest": file_digest(record_dir / "axiom-report.cjson"),
        "certificationReceiptDigest": receipt_binding_digest,
        "environmentLockDigest": receipt.get("environmentLockDigest"),
    }
    cert_digest = sha256_digest(binding)
    receipt["certificationRecordDigest"] = cert_digest
    write_cjson(record_dir / "certification-receipt.cjson", receipt)

    relative_files = [
        "replay-target.cjson",
        "checker-evaluation.cjson",
        "theorem-identity.cjson",
        "axiom-report.cjson",
        "certification-receipt.cjson",
    ]
    if signature is not None:
        relative_files.append("signature.cjson")
    files_meta = _file_entries(record_dir, relative_files)
    _reject_duplicate_roles(files_meta)

    manifest: dict[str, Any] = {
        "bundleVersion": BUNDLE_VERSION,
        "schemaVersion": BUNDLE_VERSION,
        "artifactKind": "certification",
        "candidateBundleDigest": candidate_bundle_digest,
        "capability": {"id": capability_id, "version": capability_version},
        "requestDigest": request_digest,
        "claimClass": claim_class,
        "resultStatus": result_status,
        "assuranceMode": assurance_mode,
        "files": files_meta,
        "provenance": {
            "leanVersion": (receipt.get("toolchain") or {}).get(
                "leanVersion", "unknown"
            ),
            "libraryRevision": "workspace",
            "checkerVersion": (receipt.get("checker") or {}).get("version", "0.1.0"),
        },
        "certificationDigest": cert_digest,
        "bundleDigest": cert_digest,
    }
    store.validate("certification-record.schema.json", manifest)
    write_cjson(record_dir / "manifest.cjson", manifest)
    return manifest


def _schemas_for_capability(capability: str) -> tuple[str, str]:
    if capability == "algebra.linear_algebra":
        return (
            "linear-algebra-request.schema.json",
            "linear-algebra-certificate.schema.json",
        )
    if capability == "logic.finite_counterexample":
        return (
            "finite-counterexample-request.schema.json",
            "finite-counterexample-certificate.schema.json",
        )
    if capability == "algebra.formal_rational_calculus":
        return (
            "symbolic-calculus-request.schema.json",
            "symbolic-calculus-certificate.schema.json",
        )
    if capability == "algebra.ideal_membership_witness":
        return (
            "ideal-membership-request.schema.json",
            "ideal-membership-certificate.schema.json",
        )
    return (
        "rational-equality-request.schema.json",
        "rational-equality-certificate.schema.json",
    )


def _listed_paths(manifest: dict[str, Any]) -> set[str]:
    return {
        str(e["path"]).replace("\\", "/")
        for e in manifest.get("files") or []
        if isinstance(e, dict) and "path" in e
    }


def verify_strict_listed_closure(
    bundle_dir: Path, manifest: dict[str, Any], *, strict: bool = True
) -> None:
    """Reject unknown unlisted files in release/strict mode."""
    if not strict:
        return
    listed = _listed_paths(manifest)
    listed.add("manifest.cjson")
    listed.add("manifest.json")
    for path in bundle_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(bundle_dir).as_posix()
        if rel in listed:
            continue
        # Ignore ephemeral OS junk only if not strict — in strict, reject all.
        raise ValueError(f"unlisted file in bundle (strict closure): {rel}")


def verify_bundle_offline(
    bundle_dir: Path,
    *,
    schemas: SchemaStore | None = None,
    strict: bool = True,
) -> list[str]:
    """Validate schemas + digests without starting backends. Returns warnings.

    Accepts v0.3 Candidate Bundles, Certification Records, and legacy v0.1/v0.2.
    Rejects placeholder theorem/axiom content (ME-RV-002).
    """
    store = schemas or SchemaStore()
    warnings: list[str] = []
    manifest_path = find_role_path(bundle_dir, "manifest")
    if manifest_path is None:
        raise FileNotFoundError(f"missing manifest.cjson/manifest.json under {bundle_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = manifest.get("bundleVersion")
    artifact_kind = manifest.get("artifactKind", "candidate")

    if artifact_kind == "certification" or version == BUNDLE_VERSION and "candidateBundleDigest" in manifest:
        store.validate("certification-record.schema.json", manifest)
        return _verify_certification_dir(bundle_dir, manifest, store=store, strict=strict)

    store.validate("evidence-bundle.schema.json", manifest)

    if version not in {BUNDLE_VERSION, BUNDLE_VERSION_V02, BUNDLE_VERSION_LEGACY}:
        warnings.append(f"unexpected bundleVersion {version!r}")

    from adapters.common.errors import AdapterError
    from adapters.common.security_bounds import reject_path_traversal

    roles_seen: set[str] = set()
    for entry in manifest["files"]:
        rel = entry["path"]
        try:
            reject_path_traversal(rel, root=bundle_dir)
        except AdapterError as exc:
            raise ValueError(str(exc)) from exc
        path = bundle_dir / rel
        if not path.is_file():
            raise FileNotFoundError(f"missing bundle file: {rel}")
        actual = file_digest(path)
        if actual != entry["digest"]:
            raise ValueError(f"digest mismatch for {rel}: {actual} != {entry['digest']}")

        role = entry.get("role") or role_from_path(rel)
        if role not in {"other", "readme", "signature"}:
            if role in roles_seen:
                raise ValueError(f"duplicate bundle role: {role}")
            roles_seen.add(role)

        if rel.endswith("theorem.lean") or rel == "theorem.lean":
            text = path.read_text(encoding="utf-8")
            if PLACEHOLDER_THEOREM_NAME in text:
                raise ValueError(
                    f"placeholder theorem rejected in {rel}: {PLACEHOLDER_THEOREM_NAME}"
                )
        if "axiom-report" in rel:
            try:
                axiom = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"axiom-report JSON invalid in {rel}: {exc}") from exc
            if isinstance(axiom, dict) and axiom.get("status") == PLACEHOLDER_AXIOM_STATUS:
                raise ValueError(
                    f"placeholder axiom report rejected in {rel}: {PLACEHOLDER_AXIOM_STATUS}"
                )

    if version == BUNDLE_VERSION:
        for required in CANDIDATE_MANDATORY_ROLES:
            if required not in roles_seen:
                raise ValueError(f"Candidate Bundle missing mandatory role: {required}")
        if manifest.get("resultStatus") != "computed":
            raise ValueError("Candidate Bundle resultStatus must be computed")
        if manifest.get("artifactKind", "candidate") != "candidate":
            raise ValueError("Candidate Bundle artifactKind must be candidate")
        expected_digest = compute_bundle_digest(manifest)
        declared = manifest.get("bundleDigest")
        if declared != expected_digest:
            raise ValueError(
                f"bundleDigest mismatch: {declared} != {expected_digest}"
            )
        verify_strict_listed_closure(bundle_dir, manifest, strict=strict)

    request = load_role_json(bundle_dir, "request")
    certificate = load_role_json(bundle_dir, "certificate")
    cap = request.get("capability", "")
    req_schema, cert_schema = _schemas_for_capability(cap if isinstance(cap, str) else "")
    store.validate(req_schema, request)
    store.validate(cert_schema, certificate)

    if request["requestDigest"] != manifest["requestDigest"]:
        raise ValueError("manifest.requestDigest != request.requestDigest")
    if certificate["requestDigest"] != request["requestDigest"]:
        raise ValueError("certificate.requestDigest != request.requestDigest")

    if manifest.get("resultStatus") in VERIFIED_RESULT_STATUSES:
        if version == BUNDLE_VERSION:
            raise ValueError("Candidate Bundle cannot claim verified status")
        receipt_path = find_role_path(bundle_dir, "checker-receipt")
        if receipt_path is None:
            raise ValueError(
                "manifest claims verified status without checker-receipt.cjson/json"
            )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict) or receipt.get("claimEstablished") in (
            None,
            "",
            False,
        ):
            raise ValueError(
                "manifest claims verified status without claimEstablished on checker-receipt"
            )
        if receipt.get("assuranceMode") == "native_checked":
            raise ValueError(
                "manifest claims verified status but checker-receipt is native_checked only"
            )
        if receipt.get("resultStatus") == "checker_accepted":
            raise ValueError(
                "manifest claims verified status but checker-receipt is checker_accepted only"
            )

    from adapters.common.canonical import verify_request_digest
    from adapters.common.lean_mirrors import (
        check_finite_counterexample,
        check_linear_algebra,
        check_symbolic_calculus,
    )

    try:
        verify_request_digest(request)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"request digest verification failed: {exc}") from exc

    if cap == "algebra.linear_algebra":
        if not check_linear_algebra(request, certificate):
            warnings.append("Python linear-algebra checker mirror rejected certificate")
    elif cap == "logic.finite_counterexample":
        if not check_finite_counterexample(request, certificate):
            warnings.append("Python finite-counterexample checker mirror rejected certificate")
    elif cap == "algebra.formal_rational_calculus":
        if not check_symbolic_calculus(request, certificate):
            warnings.append("Python symbolic-calculus checker mirror rejected certificate")

    return warnings


def _verify_certification_dir(
    record_dir: Path,
    manifest: dict[str, Any],
    *,
    store: SchemaStore,
    strict: bool,
) -> list[str]:
    warnings: list[str] = []
    from adapters.common.errors import AdapterError
    from adapters.common.security_bounds import reject_path_traversal

    roles_seen: set[str] = set()
    for entry in manifest["files"]:
        rel = entry["path"]
        try:
            reject_path_traversal(rel, root=record_dir)
        except AdapterError as exc:
            raise ValueError(str(exc)) from exc
        path = record_dir / rel
        if not path.is_file():
            raise FileNotFoundError(f"missing certification file: {rel}")
        actual = file_digest(path)
        if actual != entry["digest"]:
            raise ValueError(f"digest mismatch for {rel}: {actual} != {entry['digest']}")
        role = entry.get("role") or role_from_path(rel)
        if role not in {"other", "readme", "signature"}:
            if role in roles_seen:
                raise ValueError(f"duplicate certification role: {role}")
            roles_seen.add(role)
        if "axiom-report" in rel:
            axiom = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(axiom, dict) and axiom.get("status") == PLACEHOLDER_AXIOM_STATUS:
                raise ValueError(
                    f"placeholder axiom report rejected in {rel}: {PLACEHOLDER_AXIOM_STATUS}"
                )
        if "theorem-identity" in rel or rel.endswith("theorem.lean"):
            text = path.read_text(encoding="utf-8")
            if PLACEHOLDER_THEOREM_NAME in text:
                raise ValueError(
                    f"placeholder theorem rejected in {rel}: {PLACEHOLDER_THEOREM_NAME}"
                )

    for required in CERTIFICATION_MANDATORY_ROLES:
        if required not in roles_seen:
            raise ValueError(f"Certification Record missing mandatory role: {required}")

    verify_strict_listed_closure(record_dir, manifest, strict=strict)
    receipt = load_role_json(record_dir, "certification-receipt")
    store.validate("certification-receipt.schema.json", receipt)
    _check_receipt_coherence(receipt)
    return warnings


def _check_receipt_coherence(receipt: dict[str, Any]) -> None:
    mode = receipt.get("assuranceMode")
    status = receipt.get("resultStatus")
    if mode == "native_checked" and status in VERIFIED_RESULT_STATUSES:
        raise ValueError("native_checked must not report soundness_verified / verified status")
    if mode == "kernel_replay":
        for key in ("theoremTypeDigest", "proofDeclarationDigest"):
            dig = receipt.get(key)
            if not isinstance(dig, str) or not dig.startswith("sha256:"):
                raise ValueError(f"kernel_replay requires {key}")
    if status in VERIFIED_RESULT_STATUSES and receipt.get("claimEstablished") in (
        None,
        "",
        False,
    ):
        raise ValueError("verified result requires claimEstablished")
    if status in VERIFIED_RESULT_STATUSES and receipt.get("unresolvedObligations"):
        raise ValueError("verified result forbids unresolved obligations")
