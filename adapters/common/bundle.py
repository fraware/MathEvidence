"""Evidence bundle helpers (Python orchestration; Lean checker is separate)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adapters.common.canonical import canonical_dumps, sha256_digest, sha256_hex
from adapters.common.schema_validate import SchemaStore

BUNDLE_VERSION = "0.1.0"


def file_digest(path: Path) -> str:
    data = path.read_bytes()
    return "sha256:" + sha256_hex(data)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Pretty for humans; digests use file bytes as stored.
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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
) -> dict[str, Any]:
    return {
        "bundleVersion": BUNDLE_VERSION,
        "capability": {"id": capability_id, "version": capability_version},
        "requestDigest": request_digest,
        "claimClass": claim_class,
        "resultStatus": result_status,
        "assuranceMode": assurance_mode,
        "files": files,
        "provenance": provenance,
    }


def write_bundle(
    bundle_dir: Path,
    *,
    request: dict[str, Any],
    candidate: dict[str, Any],
    certificate: dict[str, Any],
    result_status: str = "computed",
    claim_class: str = "candidate",
    assurance_mode: str = "kernel_replay",
    lean_version: str = "4.x-pending",
    library_revision: str = "workspace",
    checker_version: str = "0.1.0",
    readme: str | None = None,
    schemas: SchemaStore | None = None,
) -> dict[str, Any]:
    """Write an EvidenceBundle directory and return the manifest."""
    store = schemas or SchemaStore()
    cap = request.get("capability")
    req_schema, cert_schema = _schemas_for_capability(cap if isinstance(cap, str) else "")
    store.validate(req_schema, request)
    store.validate(cert_schema, certificate)

    bundle_dir.mkdir(parents=True, exist_ok=True)
    write_json(bundle_dir / "request.json", request)
    write_json(bundle_dir / "candidate.json", candidate)
    write_json(bundle_dir / "certificate.json", certificate)
    if readme is None:
        readme = (
            f"# Evidence bundle\n\n"
            f"Offline-replayable candidate evidence for `{cap}`.\n"
            "Adapter output is untrusted; Lean checkers own theorem acceptance.\n"
        )
    (bundle_dir / "README.md").write_text(readme, encoding="utf-8")

    relative_files = ["request.json", "candidate.json", "certificate.json", "README.md"]
    files_meta = []
    for name in relative_files:
        path = bundle_dir / name
        media = "text/markdown" if name.endswith(".md") else "application/json"
        files_meta.append(
            {
                "path": name,
                "digest": file_digest(path),
                "mediaType": media,
            }
        )

    manifest = build_manifest(
        capability_id=request["capability"],
        capability_version=request["capabilityVersion"],
        request_digest=request["requestDigest"],
        claim_class=claim_class,
        result_status=result_status,
        assurance_mode=assurance_mode,
        files=files_meta,
        provenance={
            "leanVersion": lean_version,
            "libraryRevision": library_revision,
            "checkerVersion": checker_version,
            "backend": certificate.get("provenance"),
        },
    )
    store.validate("evidence-bundle.schema.json", manifest)
    write_json(bundle_dir / "manifest.json", manifest)
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
    if capability == "analysis.symbolic_calculus":
        return (
            "symbolic-calculus-request.schema.json",
            "symbolic-calculus-certificate.schema.json",
        )
    return (
        "rational-equality-request.schema.json",
        "rational-equality-certificate.schema.json",
    )


def verify_bundle_offline(bundle_dir: Path, *, schemas: SchemaStore | None = None) -> list[str]:
    """Validate schemas + digests without starting backends. Returns warnings."""
    store = schemas or SchemaStore()
    warnings: list[str] = []
    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    store.validate("evidence-bundle.schema.json", manifest)

    for entry in manifest["files"]:
        rel = entry["path"]
        if ".." in rel.split("/") or rel.startswith("/"):
            raise ValueError(f"path traversal rejected: {rel}")
        path = bundle_dir / rel
        if not path.is_file():
            raise FileNotFoundError(f"missing bundle file: {rel}")
        actual = file_digest(path)
        if actual != entry["digest"]:
            raise ValueError(f"digest mismatch for {rel}: {actual} != {entry['digest']}")

    request = json.loads((bundle_dir / "request.json").read_text(encoding="utf-8"))
    certificate = json.loads((bundle_dir / "certificate.json").read_text(encoding="utf-8"))
    cap = request.get("capability", "")
    req_schema, cert_schema = _schemas_for_capability(cap if isinstance(cap, str) else "")
    store.validate(req_schema, request)
    store.validate(cert_schema, certificate)

    if request["requestDigest"] != manifest["requestDigest"]:
        raise ValueError("manifest.requestDigest != request.requestDigest")
    if certificate["requestDigest"] != request["requestDigest"]:
        raise ValueError("certificate.requestDigest != request.requestDigest")

    from adapters.common.canonical import verify_request_digest
    from adapters.common.lean_mirrors import (
        check_finite_counterexample,
        check_linear_algebra,
        check_symbolic_calculus,
    )

    try:
        verify_request_digest(request)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"request digest verification failed: {exc}")

    if cap == "algebra.linear_algebra":
        if not check_linear_algebra(request, certificate):
            warnings.append("Python linear-algebra checker mirror rejected certificate")
    elif cap == "logic.finite_counterexample":
        if not check_finite_counterexample(request, certificate):
            warnings.append("Python finite-counterexample checker mirror rejected certificate")
    elif cap == "analysis.symbolic_calculus":
        if not check_symbolic_calculus(request, certificate):
            warnings.append("Python symbolic-calculus checker mirror rejected certificate")

    _ = canonical_dumps
    _ = sha256_digest
    return warnings
