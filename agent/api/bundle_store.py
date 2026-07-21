"""Root-jailed bundle storage helpers for the Agent API."""

from __future__ import annotations

import os
import re
import secrets
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


class BundlePathError(ValueError):
    """Raised when a bundle reference would escape the configured jail."""


_BUNDLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_CONTENT_ID_RE = re.compile(r"^sha256_([0-9a-f]{64})$")
# Legacy path open/write is confined to evidence + agent store — never arbitrary repo paths.
_ALLOWED_LEGACY_PREFIXES = ("evidence/", "agent/store/")


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


class BundleStore:
    """Resolve bundle paths and opaque ids under explicit filesystem roots.

    Preferred references:
    - ``bundleId`` under ``agent/store/bundles``
    - content-addressed ``sha256_<hex>`` under ``evidence/store/sha256/<aa>/<rest>/``

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

    def content_addressed_dir(self, digest: str) -> Path:
        """Return ``evidence/store/sha256/<aa>/<rest>/`` for a sha256 digest."""
        if not digest.startswith("sha256:") or len(digest) != 71:
            raise BundlePathError("content digest must be sha256:<64 hex>")
        hex_body = digest[7:].lower()
        if any(c not in "0123456789abcdef" for c in hex_body):
            raise BundlePathError("content digest hex must be lowercase")
        path = (
            self.evidence_store_root / "sha256" / hex_body[:2] / hex_body[2:]
        ).resolve()
        self._require_under_root(path, self.evidence_store_root)
        return path

    def allocate_content_addressed_bundle_id(self, digest: str) -> str:
        """Opaque id derived from content digest (not a filesystem path)."""
        if not digest.startswith("sha256:") or len(digest) != 71:
            raise BundlePathError("content digest must be sha256:<64 hex>")
        hex_body = digest[7:].lower()
        if any(c not in "0123456789abcdef" for c in hex_body):
            raise BundlePathError("content digest hex must be lowercase")
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
        content = _CONTENT_ID_RE.fullmatch(safe_id)
        if content:
            digest = f"sha256:{content.group(1)}"
            path = self.content_addressed_dir(digest)
            # Bundle payload lives in the content-addressed directory itself.
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
        # Extra containment: evidence paths under evidence/, store under agent/store.
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

    def commit_content_addressed(
        self, bundle_dir: Path, *, request_digest: str
    ) -> tuple[Path, str]:
        """Copy a written bundle into the content-addressed store.

        Returns ``(store_path, opaque_bundle_id)``. The store directory is keyed
        by the request digest (stable identity for the request binding).
        """
        store_path = self.content_addressed_dir(request_digest)
        opaque_id = self.allocate_content_addressed_bundle_id(request_digest)
        if store_path.exists():
            # Idempotent: existing content-addressed entry wins.
            return store_path, opaque_id
        store_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = store_path.with_name(store_path.name + f".tmp-{secrets.token_hex(4)}")
        try:
            shutil.copytree(bundle_dir, tmp)
            os.replace(tmp, store_path)
        except Exception:
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)
            raise
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
