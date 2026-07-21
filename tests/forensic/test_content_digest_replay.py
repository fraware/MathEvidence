"""Forensic: content digests must be verified before replay trust."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adapters.common.bundle import (
    find_role_path,
    file_digest,
    load_role_json,
    verify_bundle_offline,
)
from adapters.common.canonical import canonical_dumps
from adapters.common.replay import run_lean_replay
from agent.api import service
from agent.api.bundle_store import BundleStore

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "evidence" / "examples" / "rational_equality_basic"


def test_verify_bundle_offline_detects_tampered_certificate() -> None:
    store_dest = ROOT / "agent" / "store" / "bundles" / "forensic_tamper_cert"
    if store_dest.exists():
        shutil.rmtree(store_dest)
    shutil.copytree(EXAMPLE, store_dest)
    try:
        cert_path = find_role_path(store_dest, "certificate")
        assert cert_path is not None
        data = json.loads(cert_path.read_text(encoding="utf-8"))
        data["_tamper"] = "evil"
        if cert_path.suffix == ".cjson":
            cert_path.write_text(canonical_dumps(data), encoding="utf-8")
        else:
            cert_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="digest mismatch"):
            verify_bundle_offline(store_dest)
    finally:
        if store_dest.exists():
            shutil.rmtree(store_dest)


def test_run_lean_replay_rejects_tampered_bundle() -> None:
    store_dest = ROOT / "agent" / "store" / "bundles" / "forensic_tamper_replay"
    if store_dest.exists():
        shutil.rmtree(store_dest)
    shutil.copytree(EXAMPLE, store_dest)
    try:
        cert_path = find_role_path(store_dest, "certificate")
        assert cert_path is not None
        data = json.loads(cert_path.read_text(encoding="utf-8"))
        data["_tamper"] = "evil"
        if cert_path.suffix == ".cjson":
            cert_path.write_text(canonical_dumps(data), encoding="utf-8")
        else:
            cert_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="digest mismatch"):
            run_lean_replay(bundle_dir=store_dest, repo_root=ROOT)
    finally:
        if store_dest.exists():
            shutil.rmtree(store_dest)


def test_content_addressed_bundle_id_resolves() -> None:
    store = BundleStore.default(ROOT)
    manifest = load_role_json(EXAMPLE, "manifest")
    digest = manifest["requestDigest"]
    assert digest.startswith("sha256:")
    opaque = store.allocate_content_addressed_bundle_id(digest)
    dest, bid = store.commit_content_addressed(EXAMPLE, request_digest=digest)
    assert bid == opaque
    assert dest.is_dir()
    assert find_role_path(dest, "manifest") is not None
    # Packaging open without a Lean receipt must not advertise claimEstablished.
    for name in ("checker-receipt.json", "checker-receipt.cjson"):
        p = dest / name
        if p.is_file():
            p.unlink()
    resolved = store.path_for_bundle_id(opaque)
    assert resolved == dest
    opened = service.op_open_bundle({"bundleId": opaque})
    assert opened["resultStatus"] in {"computed", "tested", "ambiguous"} or (
        opened.get("error") is None
    )
    assert opened.get("claimEstablished") is None
    if dest.exists():
        shutil.rmtree(dest)


def test_honest_example_digests_match_files() -> None:
    manifest = load_role_json(EXAMPLE, "manifest")
    for entry in manifest["files"]:
        path = EXAMPLE / entry["path"]
        assert path.is_file()
        assert file_digest(path) == entry["digest"]
