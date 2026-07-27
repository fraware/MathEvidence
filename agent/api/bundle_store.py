"""Root-jailed bundle storage helpers for the Agent API (Wave 1 / ME-RV-011).

Content addressing keys by **bundle digest** (not request digest):

  evidence/store/bundles/sha256/<aa>/<rest>/
  evidence/store/certifications/sha256/<aa>/<rest>/
  evidence/store/index/by-request/<request-hex>.cjson
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal

from adapters.common.bundle import (
    compute_bundle_digest,
    file_digest,
    find_role_path,
    load_role_json,
    verify_bundle_offline,
)
from adapters.common.canonical import canonical_dumps


class BundlePathError(ValueError):
    """Raised when a bundle reference would escape the configured jail."""


class ContentAddressCollision(ValueError):
    """Raised when a digest path exists with different bytes."""

    def __init__(self, digest: str, detail: str = "") -> None:
        self.code = "content_address_collision"
        self.digest = digest
        msg = f"content_address_collision for {digest}"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)


_BUNDLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_CONTENT_ID_RE = re.compile(r"^sha256_([0-9a-f]{64})$")
_CERT_ID_RE = re.compile(r"^cert_sha256_([0-9a-f]{64})$")
# Legacy path open/write is confined to evidence + agent store — never arbitrary repo paths.
_ALLOWED_LEGACY_PREFIXES = ("evidence/", "agent/store/")

ArtifactKind = Literal["candidate", "certification"]


@dataclass(frozen=True)
class BundleStoreConfig:
    repo_root: Path
    evidence_store_root: Path
    agent_store_root: Path
    max_path_length: int = 512
    max_bundle_id_length: int = 128


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _has_parent_segment(value: str) -> bool:
    return ".." in PurePosixPath(value.replace("\\", "/")).parts


def _is_absolute_reference(value: str) -> bool:
    return (
        Path(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
        or PurePosixPath(value).is_absolute()
    )


def _normalize_rel(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def _hex_from_digest(digest: str) -> str:
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise BundlePathError("content digest must be sha256:<64 hex>")
    hex_body = digest[7:].lower()
    if any(c not in "0123456789abcdef" for c in hex_body):
        raise BundlePathError("content digest hex must be lowercase")
    return hex_body


def _dirs_byte_identical(a: Path, b: Path) -> bool:
    """Compare every regular file under both trees (relative paths + bytes)."""
    files_a = {
        p.relative_to(a).as_posix(): p
        for p in a.rglob("*")
        if p.is_file()
    }
    files_b = {
        p.relative_to(b).as_posix(): p
        for p in b.rglob("*")
        if p.is_file()
    }
    if set(files_a) != set(files_b):
        return False
    for rel, path_a in files_a.items():
        if path_a.read_bytes() != files_b[rel].read_bytes():
            return False
    return True


def _fsync_tree(root: Path) -> None:
    """Best-effort fsync of files and directories (no-op where unsupported)."""
    for path in sorted(root.rglob("*"), reverse=True):
        try:
            fd = os.open(str(path), os.O_RDONLY)
        except OSError:
            continue
        try:
            os.fsync(fd)
        except OSError:
            pass
        finally:
            os.close(fd)
    try:
        fd = os.open(str(root), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


class BundleStore:
    """Resolve bundle paths and opaque ids under explicit filesystem roots.

    Preferred references:
    - content-addressed ``sha256_<hex>`` under ``evidence/store/bundles/sha256/``
    - certification ``cert_sha256_<hex>`` under ``evidence/store/certifications/sha256/``
    - opaque ``bundleId`` under ``agent/store/bundles``

    Legacy ``path`` references are repo-relative and confined to ``evidence/``
    or ``agent/store/``. Absolute paths and parent traversal are always rejected.
    """

    def __init__(self, config: BundleStoreConfig) -> None:
        self.config = config
        self.repo_root = config.repo_root.resolve()
        self.evidence_store_root = config.evidence_store_root.resolve()
        self.agent_store_root = config.agent_store_root.resolve()

    @classmethod
    def default(cls, repo_root: Path) -> "BundleStore":
        root = repo_root.resolve()
        return cls(
            BundleStoreConfig(
                repo_root=root,
                evidence_store_root=root / "evidence" / "store",
                agent_store_root=root / "agent" / "store",
            )
        )

    def content_addressed_dir(
        self, digest: str, *, kind: ArtifactKind = "candidate"
    ) -> Path:
        """Return digest-keyed store directory for candidate or certification."""
        hex_body = _hex_from_digest(digest)
        sub = "bundles" if kind == "candidate" else "certifications"
        path = (
            self.evidence_store_root / sub / "sha256" / hex_body[:2] / hex_body[2:]
        ).resolve()
        self._require_under_root(path, self.evidence_store_root)
        return path

    def allocate_content_addressed_bundle_id(
        self, digest: str, *, kind: ArtifactKind = "candidate"
    ) -> str:
        """Opaque id derived from content digest (not a filesystem path)."""
        hex_body = _hex_from_digest(digest)
        if kind == "certification":
            return f"cert_sha256_{hex_body}"
        return f"sha256_{hex_body}"

    def allocate_bundle_id(self) -> str:
        """Allocate an opaque non-content-addressed agent store id."""
        return f"b_{secrets.token_hex(16)}"

    def validate_bundle_id(self, bundle_id: str) -> str:
        if len(bundle_id) > self.config.max_bundle_id_length:
            raise BundlePathError("bundleId exceeds configured length quota")
        if not _BUNDLE_ID_RE.fullmatch(bundle_id):
            raise BundlePathError("bundleId must be opaque and path-free")
        if bundle_id in {".", ".."}:
            raise BundlePathError("bundleId must not be a path segment")
        return bundle_id

    def path_for_bundle_id(self, bundle_id: str) -> Path:
        safe_id = self.validate_bundle_id(bundle_id)
        cert = _CERT_ID_RE.fullmatch(safe_id)
        if cert:
            digest = f"sha256:{cert.group(1)}"
            return self.content_addressed_dir(digest, kind="certification")
        content = _CONTENT_ID_RE.fullmatch(safe_id)
        if content:
            digest = f"sha256:{content.group(1)}"
            # Prefer v0.3 layout; fall back to legacy request-digest path.
            path = self.content_addressed_dir(digest, kind="candidate")
            if path.is_dir():
                return path
            legacy = (
                self.evidence_store_root / "sha256" / digest[7:9] / digest[9:]
            ).resolve()
            if legacy.is_dir():
                self._require_under_root(legacy, self.evidence_store_root)
                return legacy
            return path
        path = (self.agent_store_root / "bundles" / safe_id).resolve()
        self._require_under_root(path, self.agent_store_root)
        return path

    def resolve_legacy_path(self, value: str) -> Path:
        self._validate_relative_path(value)
        norm = _normalize_rel(value)
        if not any(norm.startswith(prefix) for prefix in _ALLOWED_LEGACY_PREFIXES):
            raise BundlePathError(
                "legacy path must be under evidence/ or agent/store/"
            )
        resolved = (self.repo_root / norm).resolve()
        self._require_under_root(resolved, self.repo_root)
        if norm.startswith("evidence/"):
            self._require_under_root(resolved, (self.repo_root / "evidence").resolve())
        else:
            self._require_under_root(resolved, self.agent_store_root)
        return resolved

    def resolve_ref(self, ref: dict[str, Any]) -> Path:
        path = ref.get("path")
        bundle_id = ref.get("bundleId")
        if isinstance(bundle_id, str) and bundle_id:
            if isinstance(path, str) and path:
                raise BundlePathError("specify either path or bundleId, not both")
            return self.path_for_bundle_id(bundle_id)
        if not isinstance(path, str) or not path:
            raise BundlePathError("bundle path or bundleId required")
        return self.resolve_legacy_path(path)

    def resolve_write_target(
        self, *, path: str | None = None, bundle_id: str | None = None
    ) -> tuple[Path, str | None]:
        if bundle_id:
            if path:
                raise BundlePathError(
                    "specify either writeBundleTo or bundleId, not both"
                )
            return self.path_for_bundle_id(bundle_id), bundle_id
        if path:
            return self.resolve_legacy_path(path), None
        generated = self.allocate_bundle_id()
        return self.path_for_bundle_id(generated), generated

    def request_index_path(self, request_digest: str) -> Path:
        hex_body = _hex_from_digest(request_digest)
        path = (
            self.evidence_store_root / "index" / "by-request" / f"{hex_body}.cjson"
        ).resolve()
        self._require_under_root(path, self.evidence_store_root)
        return path

    def read_request_index(self, request_digest: str) -> list[str]:
        path = self.request_index_path(request_digest)
        if not path.is_file():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return []
        digests = data.get("bundleDigests") or []
        return [d for d in digests if isinstance(d, str)]

    def _append_request_index(self, request_digest: str, bundle_digest: str) -> None:
        path = self.request_index_path(request_digest)
        existing = self.read_request_index(request_digest)
        if bundle_digest not in existing:
            existing.append(bundle_digest)
        payload = {
            "schemaVersion": "0.3.0",
            "requestDigest": request_digest,
            "bundleDigests": existing,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        self.atomic_write_text(path, canonical_dumps(payload))

    def certification_index_path(self, request_digest: str) -> Path:
        hex_body = _hex_from_digest(request_digest)
        path = (
            self.evidence_store_root
            / "index"
            / "by-request-certifications"
            / f"{hex_body}.cjson"
        ).resolve()
        self._require_under_root(path, self.evidence_store_root)
        return path

    def read_certification_index(self, request_digest: str) -> list[str]:
        path = self.certification_index_path(request_digest)
        if not path.is_file():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return []
        digests = data.get("certificationDigests") or []
        return [d for d in digests if isinstance(d, str)]

    def list_certifications_for_request(self, request_digest: str) -> list[str]:
        """Return opaque certification IDs for a request digest."""
        digests = self.read_certification_index(request_digest)
        return [
            self.allocate_content_addressed_bundle_id(d, kind="certification")
            for d in digests
        ]

    def _append_certification_index(
        self, request_digest: str, certification_digest: str
    ) -> None:
        path = self.certification_index_path(request_digest)
        existing = self.read_certification_index(request_digest)
        if certification_digest not in existing:
            existing.append(certification_digest)
        payload = {
            "schemaVersion": "0.3.0",
            "requestDigest": request_digest,
            "certificationDigests": existing,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        self.atomic_write_text(path, canonical_dumps(payload))

    def commit_content_addressed(
        self,
        bundle_dir: Path,
        *,
        request_digest: str | None = None,
        bundle_digest: str | None = None,
        kind: ArtifactKind = "candidate",
        verify: bool = True,
    ) -> tuple[Path, str]:
        """Copy a written artifact into the content-addressed store.

        Keyed by **bundle digest** (manifest binding payload digest).
        Byte-identical recommit is idempotent; differing bytes raise
        ``ContentAddressCollision``.

        Returns ``(store_path, opaque_bundle_id)``.
        """
        if verify:
            verify_bundle_offline(bundle_dir, strict=True)

        manifest_path = find_role_path(bundle_dir, "manifest")
        if manifest_path is None:
            raise BundlePathError("missing manifest for content-addressed commit")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        if kind == "certification":
            digest = (
                bundle_digest
                or manifest.get("certificationDigest")
                or manifest.get("bundleDigest")
            )
        else:
            digest = bundle_digest or manifest.get("bundleDigest")
            if not digest:
                digest = compute_bundle_digest(manifest)

        if not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise BundlePathError("bundle digest missing or invalid for commit")

        req = request_digest or manifest.get("requestDigest")
        if not isinstance(req, str) or not req.startswith("sha256:"):
            raise BundlePathError("request digest missing or invalid for commit")

        store_path = self.content_addressed_dir(digest, kind=kind)
        opaque_id = self.allocate_content_addressed_bundle_id(digest, kind=kind)

        if store_path.exists():
            if _dirs_byte_identical(bundle_dir, store_path):
                if kind == "candidate":
                    self._append_request_index(req, digest)
                else:
                    self._append_certification_index(req, digest)
                return store_path, opaque_id
            raise ContentAddressCollision(
                digest, "existing store path has different bytes"
            )

        store_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = store_path.with_name(store_path.name + f".tmp-{secrets.token_hex(4)}")
        try:
            shutil.copytree(bundle_dir, tmp)
            _fsync_tree(tmp)
            os.replace(tmp, store_path)
        except Exception:
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)
            raise

        if kind == "candidate":
            self._append_request_index(req, digest)
        else:
            self._append_certification_index(req, digest)
        return store_path, opaque_id

    def atomic_write_text(
        self, path: Path, text: str, *, encoding: str = "utf-8"
    ) -> None:
        self._require_under_known_root(path.resolve())
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding=encoding) as handle:
                handle.write(text)
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except OSError:
                    pass
            os.replace(tmp_name, path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def _validate_relative_path(self, value: str) -> None:
        if len(value) > self.config.max_path_length:
            raise BundlePathError("bundle path exceeds configured length quota")
        if _is_absolute_reference(value):
            raise BundlePathError("absolute bundle paths are not allowed")
        if _has_parent_segment(value):
            raise BundlePathError("bundle path traversal is not allowed")
        if not value.strip():
            raise BundlePathError("bundle path must not be empty")

    def _require_under_root(self, path: Path, root: Path) -> None:
        if not _is_relative_to(path, root):
            raise BundlePathError(
                f"bundle path escapes configured root: {root}"
            )

    def _require_under_known_root(self, path: Path) -> None:
        roots = (
            self.repo_root,
            self.evidence_store_root,
            self.agent_store_root,
        )
        if not any(_is_relative_to(path, root) for root in roots):
            raise BundlePathError("bundle path escapes configured roots")
