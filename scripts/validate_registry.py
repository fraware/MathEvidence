#!/usr/bin/env python3
"""Validate registry capability and backend entries against schemas."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.schema_validate import SchemaStore  # noqa: E402

CAP_DIR = ROOT / "registry" / "capabilities"
BACKEND_DIR = ROOT / "registry" / "backends"
CATALOG = ROOT / "registry" / "catalog.json"
PROMOTION_DIR = ROOT / "registry" / "promotions"
_GIT_SHA = __import__("re").compile(r"^[0-9a-f]{40}$")


def _validate_schema_refs(data: dict, path: Path) -> None:
    for key in ("evidenceSchema", "requestSchema"):
        rel = data.get(key)
        if isinstance(rel, str):
            target = ROOT / rel
            if not target.is_file():
                raise FileNotFoundError(f"{path.name}: {key} missing: {rel}")
    ir = data.get("inputIR")
    if isinstance(ir, dict):
        ir_schema = ir.get("schema")
        if isinstance(ir_schema, str):
            target = ROOT / ir_schema
            if not target.is_file():
                raise FileNotFoundError(f"{path.name}: inputIR.schema missing: {ir_schema}")


def _load_promotion_record(capability_id: str, version: str) -> dict:
    """Stable capabilities MUST ship a schema-valid signed promotion record (ME-RV-087)."""
    if not PROMOTION_DIR.is_dir():
        raise FileNotFoundError(
            f"stable {capability_id}: missing registry/promotions/ "
            "(promotion-record.schema.json required)"
        )
    candidates = sorted(PROMOTION_DIR.glob(f"{capability_id}@*.json"))
    # Prefer exact version match; else any file whose capabilityId matches.
    store = SchemaStore()
    matched: dict | None = None
    for path in candidates:
        data = json.loads(path.read_text(encoding="utf-8"))
        store.validate("promotion-record.schema.json", data)
        if data.get("capabilityId") != capability_id:
            raise ValueError(f"{path.name}: capabilityId mismatch for filename")
        if data.get("capabilityVersion") == version:
            matched = data
            break
        if matched is None:
            matched = data
    if matched is None:
        # Also allow capability_id.json without @version suffix.
        plain = PROMOTION_DIR / f"{capability_id}.json"
        if plain.is_file():
            matched = json.loads(plain.read_text(encoding="utf-8"))
            store.validate("promotion-record.schema.json", matched)
        else:
            raise FileNotFoundError(
                f"stable {capability_id}: no promotion record under registry/promotions/"
            )
    if matched.get("capabilityId") != capability_id:
        raise ValueError(f"promotion record capabilityId != {capability_id}")
    commit = matched.get("releaseCommit")
    if not isinstance(commit, str) or not _GIT_SHA.match(commit):
        raise ValueError(f"stable {capability_id}: promotion releaseCommit must be 40-char SHA")
    if commit == "workspace":
        raise ValueError(f"stable {capability_id}: promotion releaseCommit must not be workspace")
    return matched


def _validate_stable_gate(data: dict, path: Path) -> None:
    if data.get("status") != "stable":
        return
    support = data.get("supportClaims") or {}
    conformance = data.get("conformance") or {}
    checker = data.get("checker") or {}
    if not support.get("conformanceVerified"):
        raise ValueError(f"{path.name}: stable requires supportClaims.conformanceVerified")
    if conformance.get("status") != "passing":
        raise ValueError(f"{path.name}: stable requires conformance.status=passing")
    if checker.get("soundnessStatus") != "present":
        raise ValueError(f"{path.name}: stable requires checker.soundnessStatus=present")
    version = str(data.get("version") or data.get("capabilityVersion") or "0.1.0")
    promo = _load_promotion_record(str(data["id"]), version)
    # Mechanically impossible to be stable without signed promotion fields.
    if not promo.get("signatures"):
        raise ValueError(f"{path.name}: promotion record missing signatures")
    print(f"ok promotion record for stable {data['id']}")


def _validate_federation(data: dict, path: Path) -> None:
    ownership = data.get("ownership", "owned")
    federation = data.get("federation")
    if ownership == "federated":
        if not isinstance(federation, dict):
            raise ValueError(f"{path.name}: federated ownership requires federation object")
        meta = federation.get("metadataSchema")
        if isinstance(meta, str) and not (ROOT / meta).is_file():
            raise FileNotFoundError(f"{path.name}: federation.metadataSchema missing: {meta}")
        note = federation.get("collaborationNote")
        if isinstance(note, str) and not (ROOT / note).is_file():
            raise FileNotFoundError(f"{path.name}: federation.collaborationNote missing: {note}")
        checker = data.get("checker") or {}
        pkg = str(checker.get("package", ""))
        if not pkg.startswith("external:"):
            raise ValueError(
                f"{path.name}: federated checker.package must start with 'external:'"
            )
        if checker.get("soundnessStatus") == "present":
            raise ValueError(
                f"{path.name}: federated capabilities must not claim MathEvidence soundness"
            )
    elif federation is not None:
        raise ValueError(f"{path.name}: federation object only allowed when ownership=federated")


def main() -> int:
    if not CAP_DIR.is_dir():
        print("registry/capabilities missing", file=sys.stderr)
        return 1
    if not BACKEND_DIR.is_dir():
        print("registry/backends missing", file=sys.stderr)
        return 1

    store = SchemaStore()
    errors = 0

    cap_files = sorted(CAP_DIR.glob("*.json"))
    if not cap_files:
        print("no capability registry entries", file=sys.stderr)
        return 1

    capability_ids: set[str] = set()
    for path in cap_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        try:
            store.validate("capability.schema.json", data)
            _validate_schema_refs(data, path)
            _validate_federation(data, path)
            _validate_stable_gate(data, path)
            cid = data["id"]
            if cid in capability_ids:
                raise ValueError(f"duplicate capability id: {cid}")
            capability_ids.add(cid)
            expected = f"{cid}.json"
            if path.name != expected:
                raise ValueError(f"filename must be {expected}")
            print(f"ok capability {path.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {path.name}: {exc}", file=sys.stderr)
            errors += 1

    backend_files = sorted(BACKEND_DIR.glob("*.json"))
    if not backend_files:
        print("no backend registry entries", file=sys.stderr)
        return 1

    backend_ids: set[str] = set()
    for path in backend_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        try:
            store.validate("backend.schema.json", data)
            bid = data["id"]
            if bid in backend_ids:
                raise ValueError(f"duplicate backend id: {bid}")
            backend_ids.add(bid)
            if path.name != f"{bid}.json":
                raise ValueError(f"filename must be {bid}.json")
            for cap in data.get("supportedCapabilities", []):
                cid = cap.get("id")
                if cid not in capability_ids:
                    raise ValueError(f"backend {bid} references unknown capability {cid!r}")
            print(f"ok backend {path.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {path.name}: {exc}", file=sys.stderr)
            errors += 1

    if CATALOG.is_file():
        try:
            catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
            for rel in catalog.get("capabilities", []):
                if not (ROOT / "registry" / rel).is_file():
                    raise FileNotFoundError(f"catalog capability missing: {rel}")
            for rel in catalog.get("backends", []):
                if not (ROOT / "registry" / rel).is_file():
                    raise FileNotFoundError(f"catalog backend missing: {rel}")
            listed_caps = {Path(r).name for r in catalog.get("capabilities", [])}
            listed_backends = {Path(r).name for r in catalog.get("backends", [])}
            on_disk_caps = {p.name for p in cap_files}
            on_disk_backends = {p.name for p in backend_files}
            if listed_caps != on_disk_caps:
                raise ValueError(
                    f"catalog capabilities mismatch: listed={sorted(listed_caps)} "
                    f"disk={sorted(on_disk_caps)}"
                )
            if listed_backends != on_disk_backends:
                raise ValueError(
                    f"catalog backends mismatch: listed={sorted(listed_backends)} "
                    f"disk={sorted(on_disk_backends)}"
                )
            print("ok catalog.json")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL catalog.json: {exc}", file=sys.stderr)
            errors += 1
    else:
        print("FAIL catalog.json missing", file=sys.stderr)
        errors += 1

    if errors:
        return 1
    print(
        f"registry-validate ok ({len(cap_files)} capabilities, {len(backend_files)} backends)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
