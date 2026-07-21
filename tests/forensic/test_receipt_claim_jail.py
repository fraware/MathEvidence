"""Forensic: claimEstablished / verified status require a content-bound receipt."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from agent.api import service

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "evidence" / "examples" / "rational_equality_basic"


def test_open_without_receipt_never_sets_claim_established() -> None:
    store_dest = ROOT / "agent" / "store" / "bundles" / "forensic_open_no_receipt"
    if store_dest.exists():
        shutil.rmtree(store_dest)
    shutil.copytree(EXAMPLE, store_dest)
    try:
        # Ensure no checker receipt
        for name in ("checker-receipt.json", "checker-receipt.cjson"):
            p = store_dest / name
            if p.exists():
                p.unlink()
        opened = service.op_open_bundle({"bundleId": "forensic_open_no_receipt"})
        assert opened.get("claimEstablished") is None
        assert opened.get("previewAccepted") in (False, None)
    finally:
        if store_dest.exists():
            shutil.rmtree(store_dest)


def test_manifest_verified_without_receipt_demotes_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "bundle"
        shutil.copytree(EXAMPLE, dest)
        store_dest = ROOT / "agent" / "store" / "bundles" / "forensic_no_receipt"
        if store_dest.exists():
            shutil.rmtree(store_dest)
        shutil.copytree(EXAMPLE, store_dest)
        try:
            from adapters.common.bundle import file_digest, find_role_path, write_cjson

            manifest_path = find_role_path(store_dest, "manifest")
            assert manifest_path is not None
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["resultStatus"] = "soundness_verified"
            for name in ("checker-receipt.json", "checker-receipt.cjson"):
                p = store_dest / name
                if p.exists():
                    p.unlink()
            # Drop receipt from manifest file list if present.
            manifest["files"] = [
                e for e in manifest["files"] if "checker-receipt" not in e.get("path", "")
            ]
            for entry in manifest["files"]:
                fp = store_dest / entry["path"]
                if fp.is_file():
                    entry["digest"] = file_digest(fp)
            if manifest_path.suffix == ".cjson":
                write_cjson(manifest_path, manifest)
            else:
                manifest_path.write_text(
                    json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
                )
            opened = service.op_open_bundle({"bundleId": "forensic_no_receipt"})
            assert opened["resultStatus"] == "computed", opened
            assert opened.get("claimEstablished") is None
            assert opened.get("previewAccepted") is False
        finally:
            if store_dest.exists():
                shutil.rmtree(store_dest)


def test_legacy_path_outside_evidence_rejected() -> None:
    out = service.op_open_bundle({"path": "MathEvidence/Core/Basic.lean"})
    assert out["resultStatus"] == "rejected"
