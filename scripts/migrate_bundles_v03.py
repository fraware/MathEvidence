#!/usr/bin/env python3
"""Migrate committed evidence trees to Candidate Bundle v0.3.

For each v0.1/v0.2 directory:
1. verify listed content bytes (skip intentional hash_mismatch fixtures);
2. discard placeholder theorem / pending axiom roles;
3. rewrite as Candidate Bundle v0.3 (status computed);
4. record legacy source path + digest in provenance;
5. remove dual .json leftovers;
6. emit a deterministic machine-readable migration report.

Certification Records are NOT synthesized here — real kernel replay is Wave 2.

Usage:
  python scripts/migrate_bundles_v03.py
  python scripts/migrate_bundles_v03.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import (  # noqa: E402
    BUNDLE_VERSION,
    PLACEHOLDER_AXIOM_STATUS,
    PLACEHOLDER_THEOREM_NAME,
    compute_bundle_digest,
    file_digest,
    find_role_path,
    iter_bundle_dirs,
    load_role_json,
    verify_bundle_offline,
    write_candidate_bundle,
)
from adapters.common.canonical import canonical_dumps  # noqa: E402

SKIP_VERIFY = {
    ROOT / "evidence" / "conformance" / "rfc0001" / "hash_mismatch" / "bundle",
    ROOT / "evidence" / "conformance" / "linear_algebra" / "hash_mismatch" / "bundle",
    ROOT
    / "evidence"
    / "conformance"
    / "finite_counterexample"
    / "hash_mismatch"
    / "bundle",
}

LEGACY_JSON_STEMS = (
    "request",
    "candidate",
    "certificate",
    "manifest",
    "provenance",
    "checker-receipt",
    "axiom-report",
)

DISCARD_FILES = (
    "theorem.lean",
    "axiom-report.cjson",
    "axiom-report.json",
    "checker-receipt.cjson",
    "checker-receipt.json",
    "receipt.cjson",
    "receipt.json",
)


def _legacy_snapshot_digest(bundle_dir: Path) -> str:
    """Stable digest over pre-migration role bytes (sorted paths)."""
    parts: list[tuple[str, str]] = []
    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(bundle_dir).as_posix()
        parts.append((rel, file_digest(path)))
    return compute_bundle_digest(
        {
            "bundleVersion": "legacy-snapshot",
            "artifactKind": "candidate",
            "capability": {"id": "migration", "version": "0.0.0"},
            "requestDigest": "sha256:" + "0" * 64,
            "claimClass": "candidate",
            "files": [
                {
                    "path": p,
                    "digest": d,
                    "mediaType": "application/octet-stream",
                    "role": "other",
                }
                for p, d in parts
            ],
            "provenance": {
                "leanVersion": "n/a",
                "libraryRevision": "n/a",
                "checkerVersion": "n/a",
            },
        }
    )


def _is_placeholder_theorem(path: Path) -> bool:
    if not path.is_file():
        return False
    return PLACEHOLDER_THEOREM_NAME in path.read_text(encoding="utf-8")


def _is_placeholder_axiom(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return isinstance(data, dict) and data.get("status") == PLACEHOLDER_AXIOM_STATUS


def migrate_one(bundle_dir: Path, *, dry_run: bool) -> dict[str, Any]:
    rel = bundle_dir.relative_to(ROOT).as_posix()
    record: dict[str, Any] = {
        "path": rel,
        "action": "migrate",
        "discarded": [],
        "bundleDigest": None,
        "error": None,
    }
    if not bundle_dir.is_dir():
        record["action"] = "skip"
        record["error"] = "missing"
        return record

    try:
        request = load_role_json(bundle_dir, "request")
        certificate = load_role_json(bundle_dir, "certificate")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        record["action"] = "refuse"
        record["error"] = str(exc)
        return record

    candidate_path = find_role_path(bundle_dir, "candidate")
    if candidate_path is None:
        candidate: dict[str, Any] = {"schemaVersion": "0.1.0", "notes": "migrated"}
    else:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        if not isinstance(candidate, dict):
            candidate = {"schemaVersion": "0.1.0", "notes": "migrated"}

    # Classify / discard placeholders before rewrite.
    discarded: list[str] = []
    for name in DISCARD_FILES:
        path = bundle_dir / name
        if not path.is_file():
            continue
        if name.startswith("theorem") and _is_placeholder_theorem(path):
            discarded.append(name)
        elif "axiom-report" in name and _is_placeholder_axiom(path):
            discarded.append(name)
        elif "checker-receipt" in name or name.startswith("receipt"):
            discarded.append(name)
        elif name.startswith("theorem"):
            # Real theorem content cannot live in Candidate Bundle — discard from
            # candidate representation (Wave 2 regenerates Certification Records).
            discarded.append(name)
        elif "axiom-report" in name:
            discarded.append(name)

    legacy_digest = _legacy_snapshot_digest(bundle_dir)
    record["discarded"] = sorted(discarded)
    record["legacySourceDigest"] = legacy_digest

    if dry_run:
        record["action"] = "dry_run"
        return record

    # Remove discarded + dual JSON before rewrite.
    for name in discarded:
        p = bundle_dir / name
        if p.is_file():
            p.unlink()
    for stem in LEGACY_JSON_STEMS:
        p = bundle_dir / f"{stem}.json"
        if p.is_file():
            p.unlink()
            discarded.append(f"{stem}.json")
    record["discarded"] = sorted(set(discarded))

    try:
        manifest = write_candidate_bundle(
            bundle_dir,
            request=request,
            candidate=candidate,
            certificate=certificate,
            claim_class="candidate",
            assurance_mode="native_checked",
            extra_provenance={
                "legacySourcePath": rel,
                "legacySourceDigest": legacy_digest,
            },
        )
    except Exception as exc:  # noqa: BLE001
        record["action"] = "refuse"
        record["error"] = str(exc)
        return record

    record["bundleDigest"] = manifest.get("bundleDigest")
    record["bundleVersion"] = manifest.get("bundleVersion")

    if bundle_dir.resolve() not in {p.resolve() for p in SKIP_VERIFY}:
        try:
            verify_bundle_offline(bundle_dir, strict=True)
        except Exception as exc:  # noqa: BLE001
            record["action"] = "verify_failed"
            record["error"] = str(exc)
            return record

    record["action"] = "migrated"
    return record


def collect_targets() -> list[Path]:
    roots = [
        ROOT / "evidence" / "examples",
        ROOT / "evidence" / "conformance",
        ROOT / "agent" / "store" / "bundles",
        ROOT / "evidence" / "store",
    ]
    seen: set[Path] = set()
    out: list[Path] = []
    for root in roots:
        for bundle in iter_bundle_dirs(root):
            # Skip ephemeral tmp commit dirs.
            if ".tmp-" in bundle.name:
                continue
            resolved = bundle.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            out.append(bundle)
    return sorted(out, key=lambda p: p.as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT
        / "docs"
        / "audits"
        / "2026-07-26-real-vision"
        / "wave1_bundle_v03_migration_report.json",
    )
    args = parser.parse_args()

    targets = collect_targets()
    records = [migrate_one(t, dry_run=args.dry_run) for t in targets]
    report = {
        "schemaVersion": "0.3.0",
        "migration": "bundles_v03",
        "dryRun": bool(args.dry_run),
        "bundleVersion": BUNDLE_VERSION,
        "count": len(records),
        "migrated": sum(1 for r in records if r["action"] == "migrated"),
        "refused": sum(1 for r in records if r["action"] == "refuse"),
        "verifyFailed": sum(1 for r in records if r["action"] == "verify_failed"),
        "records": records,
    }
    # Deterministic serialization.
    text = canonical_dumps(report)
    # Pretty for humans while keeping key order stable via re-parse.
    pretty = json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(pretty, encoding="utf-8")
    print(f"wrote {args.report} ({report['migrated']} migrated / {report['count']} total)")
    if report["refused"] or report["verifyFailed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
