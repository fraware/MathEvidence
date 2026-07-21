#!/usr/bin/env python3
"""Executable adversarial cases beyond seed catalog validation.

Exercises wrong hash, truncated cert, oversized ints, nesting bombs, and path
traversal against Python security bounds + offline bundle verification.
"""

from __future__ import annotations

import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import (  # noqa: E402
    find_role_path,
    load_role_json,
    verify_bundle_offline,
    write_bundle,
    write_cjson,
)
from adapters.common.canonical import bind_request_digest, reject_duplicate_keys  # noqa: E402
from adapters.common.errors import AdapterError  # noqa: E402
from adapters.common.limits import ResourceLimits  # noqa: E402
from adapters.common.rational_ir import expr_size  # noqa: E402
from adapters.common.security_bounds import (  # noqa: E402
    enforce_nesting_depth,
    reject_path_traversal,
    walk_enforce_integer_digits,
)

SEED = ROOT / "benchmarks" / "adversarial" / "seed"
BASIC = ROOT / "evidence" / "examples" / "rational_equality_basic"


def _load_basic() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    req = load_role_json(BASIC, "request")
    cand = load_role_json(BASIC, "candidate")
    cert = load_role_json(BASIC, "certificate")
    return req, cand, cert


def _expect_reject(name: str, fn: Callable[[], None]) -> dict[str, Any]:
    try:
        fn()
    except (AdapterError, ValueError, FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return {"id": name, "status": "pass", "rejected": True, "error": type(exc).__name__}
    return {"id": name, "status": "fail", "rejected": False, "error": None}


def case_wrong_hash() -> dict[str, Any]:
    req, cand, cert = _load_basic()
    bad = deepcopy(cert)
    bad["requestDigest"] = "sha256:" + ("ab" * 32)

    def run() -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            # Bypass write_bundle schema path: plant mismatched digest files + manifest.
            write_bundle(bundle, request=req, candidate=cand, certificate=cert)
            # Overwrite the authoritative v0.2 role (dual-read prefers .cjson).
            write_cjson(bundle / "certificate.cjson", bad)
            verify_bundle_offline(bundle)

    return _expect_reject("wrong_request_hash", run)


def case_truncated_certificate() -> dict[str, Any]:
    cert_path = find_role_path(BASIC, "certificate")
    if cert_path is None:
        raise FileNotFoundError(f"missing certificate under {BASIC}")
    raw = cert_path.read_text(encoding="utf-8")
    truncated = raw[: max(20, len(raw) // 3)]

    def run() -> None:
        json.loads(truncated)

    return _expect_reject("truncated_certificate", run)


def case_oversized_integer() -> dict[str, Any]:
    huge = "9" * 5000

    def run() -> None:
        walk_enforce_integer_digits({"tag": "int", "value": huge}, max_digits=4096)

    return _expect_reject("oversized_integer", run)


def case_excessive_nesting() -> dict[str, Any]:
    node: dict[str, Any] = {"tag": "int", "value": "1"}
    for _ in range(80):
        node = {"tag": "neg", "arg": node}

    def run() -> None:
        enforce_nesting_depth(node, limits=ResourceLimits(max_nesting_depth=64))
        expr_size(node, max_depth=64)

    return _expect_reject("excessive_nesting", run)


def case_path_traversal() -> dict[str, Any]:
    def run() -> None:
        reject_path_traversal("../etc/passwd", root=ROOT)

    return _expect_reject("path_traversal", run)


def case_duplicate_keys() -> dict[str, Any]:
    def run() -> None:
        reject_duplicate_keys('{"a":1,"a":2}')

    return _expect_reject("duplicate_keys", run)


def case_malicious_filename() -> dict[str, Any]:
    def run() -> None:
        reject_path_traversal("..\\windows\\system32\\config", root=ROOT)

    return _expect_reject("malicious_filename", run)


def case_bundle_path_traversal_manifest() -> dict[str, Any]:
    req, cand, cert = _load_basic()

    def run() -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            write_bundle(bundle, request=req, candidate=cand, certificate=cert)
            manifest = load_role_json(bundle, "manifest")
            manifest["files"].append(
                {
                    "path": "../outside.json",
                    "digest": "sha256:" + ("00" * 32),
                    "mediaType": "application/json",
                }
            )
            write_cjson(bundle / "manifest.cjson", manifest)
            verify_bundle_offline(bundle)

    return _expect_reject("bundle_path_traversal", run)


def _write_seed_payload(category: str, payload: dict[str, Any]) -> None:
    path = SEED / f"{category}.json"
    existing = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    existing.update(payload)
    existing["executable"] = True
    path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")


def refresh_seed_markers() -> None:
    """Annotate seed JSON files that now have executable coverage."""
    for cat in (
        "wrong_request_hash",
        "truncated_certificate",
        "oversized_integer",
        "excessive_nesting",
        "path_traversal",
        "duplicate_keys",
        "malicious_filename",
    ):
        _write_seed_payload(
            cat,
            {
                "notes": (
                    "Executable via scripts/run_adversarial_executable.py "
                    "(security.yml / just adversarial-exec)."
                ),
            },
        )


def main() -> int:
    refresh_seed_markers()
    results = [
        case_wrong_hash(),
        case_truncated_certificate(),
        case_oversized_integer(),
        case_excessive_nesting(),
        case_path_traversal(),
        case_duplicate_keys(),
        case_malicious_filename(),
        case_bundle_path_traversal_manifest(),
    ]
    failed = [r for r in results if r["status"] != "pass"]
    out = ROOT / "benchmarks" / "adversarial" / "executable_manifest.json"
    out.write_text(json.dumps({"version": 1, "cases": results}, indent=2) + "\n", encoding="utf-8")
    if failed:
        print("adversarial-exec FAIL:", ", ".join(r["id"] for r in failed), file=sys.stderr)
        return 1
    print(f"adversarial-exec ok ({len(results)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
