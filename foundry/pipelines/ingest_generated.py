"""Ingest FiniteGraph Foundry episode slice + conformance bundles."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from foundry.pipelines.common import REPO_ROOT, content_digest, load_json
from foundry.pipelines.ingest_evidence import _strip_optional_nones, ingest_evidence_bundle

_NS = UUID("636f6e66-6f72-6d61-6e63-6500696e6700")  # conformance-ingest v0
_FG_DIR = REPO_ROOT / "evidence" / "conjecture" / "finite_graph" / "foundry_episodes"
_CONFORMANCE_ROOT = REPO_ROOT / "evidence" / "conformance"


def ingest_finite_graph_episodes(
    episodes_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Load pre-generated FiniteGraph certified-refutation episodes."""
    root = episodes_dir or _FG_DIR
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        if path.name == "index.json":
            continue
        ep = load_json(path)
        if not isinstance(ep, dict):
            continue
        # Ensure source family tag for splits.
        prov = dict(ep.get("provenance") or {})
        prov.setdefault("sourceFamily", "finite_graph_conjecture")
        ep = {**ep, "provenance": prov}
        out.append(_strip_optional_nones(ep))
    return out


def _conformance_bundle_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    dirs: list[Path] = []
    for manifest in root.rglob("manifest.json"):
        bundle = manifest.parent
        if (bundle / "request.json").is_file() and (bundle / "certificate.json").is_file():
            dirs.append(bundle)
    return sorted(dirs)


def ingest_conformance_bundles(
    conformance_root: Path | None = None,
    *,
    repo_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Ingest conformance offline bundles that carry request+certificate."""
    root = conformance_root or _CONFORMANCE_ROOT
    rr = repo_root or REPO_ROOT
    episodes: list[dict[str, Any]] = []
    for bundle in _conformance_bundle_dirs(root):
        try:
            ep = ingest_evidence_bundle(bundle, repo_root=rr)
        except (FileNotFoundError, OSError, ValueError):
            continue
        prov = dict(ep.get("provenance") or {})
        # Derive source family from capability / path segment.
        cap = str(ep.get("toolUse", {}).get("selectedCapability") or "")
        family = {
            "algebra.rational_equality": "conformance_rational",
            "algebra.linear_algebra": "conformance_linear_algebra",
            "logic.finite_counterexample": "conformance_finite_cex",
            "algebra.formal_rational_calculus": "conformance_calculus",
            "algebra.groebner_membership": "conformance_ideal",
        }.get(cap, "conformance_other")
        if "symbolic_calculus" in str(prov.get("sourcePath") or ""):
            family = "conformance_calculus"
        if "ideal" in str(prov.get("sourcePath") or "") or "rfc0001" in str(
            prov.get("sourcePath") or ""
        ):
            family = "conformance_ideal" if "rfc0001" in str(prov.get("sourcePath") or "") else family
        prov["sourceFamily"] = family
        prov["sourceKind"] = "committed_evidence"
        prov["notes"] = (prov.get("notes") or "") + " Ingested from evidence/conformance."
        ep["provenance"] = prov
        # Stable id from path so rebuilds do not collide with examples.
        rel = str(prov.get("sourcePath") or bundle.as_posix())
        ep["episodeId"] = str(uuid5(_NS, rel))
        ep["capturedAt"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Refresh content digest after id/family mutation.
        cont = dict(ep.get("contamination") or {})
        cont["contentDigest"] = content_digest(
            {
                "capability": cap,
                "sourcePath": rel,
                "requestDigest": (ep.get("outcome") or {}).get("requestDigest"),
                "sourceFamily": family,
            }
        )
        ep["contamination"] = cont
        episodes.append(_strip_optional_nones(ep))
    return episodes
