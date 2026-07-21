#!/usr/bin/env python3
"""Prove historical EvidenceBundle replay is independent of mutable registry state.

Pins: every bundle stores capability.id + capability.version in the manifest.
This test removes/changes the *current* registry capability entry and asserts
committed offline bundles still verify.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import load_role_json, verify_bundle_offline  # noqa: E402

PINNED_BUNDLES = [
    ROOT / "evidence" / "examples" / "rational_equality_basic",
    ROOT / "evidence" / "examples" / "linear_algebra_inverse_2x2",
    ROOT / "evidence" / "examples" / "finite_counterexample_nat_eq0",
]


def _assert_version_pin(bundle: Path) -> dict:
    manifest = load_role_json(bundle, "manifest")
    cap = manifest.get("capability") or {}
    if not isinstance(cap.get("id"), str) or not isinstance(cap.get("version"), str):
        raise AssertionError(f"{bundle}: manifest missing capability.id/version pin")
    request = load_role_json(bundle, "request")
    if request.get("capabilityVersion") != cap["version"]:
        raise AssertionError(
            f"{bundle}: request.capabilityVersion != manifest.capability.version"
        )
    return manifest


def _mutate_registry_copy(tmp: Path) -> None:
    """Remove/change current rational_equality entry in a temporary registry tree."""
    src = ROOT / "registry"
    dst = tmp / "registry"
    shutil.copytree(src, dst)
    cap_path = dst / "capabilities" / "algebra.rational_equality.json"
    if not cap_path.is_file():
        raise FileNotFoundError(cap_path)
    # Simulate "current entry removed/changed": bump version + wipe conformance.
    data = json.loads(cap_path.read_text(encoding="utf-8"))
    data["version"] = "9.9.9"
    data["status"] = "deprecated"
    data["conformanceVerified"] = False
    cap_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    # Also remove a catalog pointer if present (best-effort).
    catalog = dst / "catalog.json"
    if catalog.is_file():
        cat = json.loads(catalog.read_text(encoding="utf-8"))
        caps = cat.get("capabilities")
        if isinstance(caps, list):
            cat["capabilities"] = [
                c
                for c in caps
                if not (
                    isinstance(c, dict)
                    and c.get("id") == "algebra.rational_equality"
                    and c.get("version") == "0.1.0"
                )
            ]
            catalog.write_text(json.dumps(cat, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    for bundle in PINNED_BUNDLES:
        if not bundle.is_dir():
            print(f"FAIL missing bundle {bundle}", file=sys.stderr)
            return 1
        _assert_version_pin(bundle)

    # Baseline replay against live tree.
    for bundle in PINNED_BUNDLES:
        warnings = verify_bundle_offline(bundle)
        if warnings:
            print(f"FAIL baseline warnings {bundle}: {warnings}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="me_registry_hist_") as td:
        tmp = Path(td)
        _mutate_registry_copy(tmp)
        # Offline replay must NOT consult registry JSON — mutate must be irrelevant.
        mutated_cap = tmp / "registry" / "capabilities" / "algebra.rational_equality.json"
        mutated = json.loads(mutated_cap.read_text(encoding="utf-8"))
        assert mutated["version"] == "9.9.9"

        for bundle in PINNED_BUNDLES:
            warnings = verify_bundle_offline(bundle)
            if warnings:
                print(
                    f"FAIL historical replay after registry mutation {bundle}: {warnings}",
                    file=sys.stderr,
                )
                return 1
            print(f"ok historical-replay {bundle.relative_to(ROOT)}")

    print("ok registry_historical_replay_independent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
