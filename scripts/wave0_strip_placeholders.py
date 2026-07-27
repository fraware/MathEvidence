#!/usr/bin/env python3
"""Wave 0 / ME-RV-002: strip placeholder theorem/axiom roles from evidence trees.

Rewrites manifests as candidate-only (computed / native_checked) and removes
overclaiming checker receipts that asserted kernel_replay/soundness_verified
without a Certification Record.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.common.bundle import (  # noqa: E402
    PLACEHOLDER_AXIOM_STATUS,
    PLACEHOLDER_THEOREM_NAME,
    VERIFIED_RESULT_STATUSES,
    file_digest,
    find_role_path,
    iter_bundle_dirs,
    write_cjson,
)

SCAN_ROOTS = [
    ROOT / "evidence" / "examples",
    ROOT / "evidence" / "conformance",
    ROOT / "agent" / "store" / "bundles",
]


def _media_type(name: str) -> str:
    if name.endswith(".md"):
        return "text/markdown"
    if name.endswith(".lean"):
        return "text/x-lean"
    if name.endswith(".cjson"):
        return "application/cjson"
    return "application/json"


def migrate_bundle(bundle_dir: Path) -> list[str]:
    actions: list[str] = []
    manifest_path = find_role_path(bundle_dir, "manifest")
    if manifest_path is None:
        return actions
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        return actions

    removed: list[str] = []

    theorem_path = bundle_dir / "theorem.lean"
    if theorem_path.is_file():
        text = theorem_path.read_text(encoding="utf-8")
        if PLACEHOLDER_THEOREM_NAME in text:
            theorem_path.unlink()
            removed.append("theorem.lean")
            actions.append(f"removed placeholder theorem.lean")

    for stem in ("axiom-report.cjson", "axiom-report.json"):
        axiom_path = bundle_dir / stem
        if not axiom_path.is_file():
            continue
        try:
            axiom = json.loads(axiom_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(axiom, dict) and axiom.get("status") == PLACEHOLDER_AXIOM_STATUS:
            axiom_path.unlink()
            removed.append(stem)
            actions.append(f"removed placeholder {stem}")

    receipt_path = find_role_path(bundle_dir, "checker-receipt")
    if receipt_path is not None:
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            receipt = None
        if isinstance(receipt, dict):
            # Prefer v0.2 cjson manifest path.
            overclaim = (
                receipt.get("assuranceMode") == "kernel_replay"
                or receipt.get("resultStatus") in VERIFIED_RESULT_STATUSES
                or (
                    receipt.get("claimEstablished") not in (None, "", False)
                    and receipt.get("resultStatus") != "checker_accepted"
                )
            )
            # Wave 0: drop receipts that overclaim theorem status from checkBool-only path.
            if overclaim:
                receipt_path.unlink()
                removed.append(receipt_path.name)
                actions.append(
                    f"removed overclaiming {receipt_path.name} "
                    f"(status={receipt.get('resultStatus')}, mode={receipt.get('assuranceMode')})"
                )
    files = manifest.get("files")
    if not isinstance(files, list):
        files = []
    new_files = []
    for entry in files:
        if not isinstance(entry, dict):
            continue
        rel = entry.get("path")
        if not isinstance(rel, str):
            continue
        if rel in removed or any(rel.endswith(r) for r in removed):
            continue
        path = bundle_dir / rel
        if not path.is_file():
            actions.append(f"dropped missing file entry {rel}")
            continue
        new_files.append(
            {
                "path": rel,
                "digest": file_digest(path),
                "mediaType": entry.get("mediaType") or _media_type(rel),
            }
        )

    changed = False
    if manifest.get("resultStatus") in VERIFIED_RESULT_STATUSES:
        manifest["resultStatus"] = "computed"
        actions.append("downgraded resultStatus to computed")
        changed = True
    if manifest.get("assuranceMode") == "kernel_replay":
        # Candidate-only without Certification Record.
        receipt_still = find_role_path(bundle_dir, "checker-receipt")
        if receipt_still is None:
            manifest["assuranceMode"] = "native_checked"
            actions.append("downgraded assuranceMode to native_checked")
            changed = True

    if removed or changed or new_files != files:
        manifest["files"] = new_files
        # Prefer v0.2 cjson manifest path.
        out = bundle_dir / "manifest.cjson"
        write_cjson(out, manifest)
        legacy = bundle_dir / "manifest.json"
        if legacy.is_file() and out != legacy:
            # Keep dual-read trees consistent when both existed; prefer cjson.
            pass
        if manifest_path.name == "manifest.json" and not out.exists():
            write_cjson(out, manifest)
        elif manifest_path.suffix == ".json" and out.is_file():
            # Replaced json with cjson for migrated trees that already had cjson.
            pass
        actions.append("rewrote manifest")
    return actions


def main() -> int:
    all_actions: dict[str, list[str]] = {}
    for root in SCAN_ROOTS:
        if not root.is_dir():
            continue
        for bundle in iter_bundle_dirs(root):
            actions = migrate_bundle(bundle)
            if actions:
                rel = str(bundle.relative_to(ROOT)).replace("\\", "/")
                all_actions[rel] = actions
    report = {
        "schemaVersion": "0.1.0",
        "wave": "0",
        "issue": "ME-RV-002",
        "bundlesMigrated": len(all_actions),
        "actions": all_actions,
    }
    out = ROOT / "docs" / "audits" / "2026-07-26-real-vision" / "wave0_placeholder_migration_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"migrated {len(all_actions)} bundles; report -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
