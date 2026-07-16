#!/usr/bin/env python3
"""Differential backend harness (TESTING_AND_CI.md §2.3).

Identical rational-equality requests are sent to SymPy and Mathematica.
Outcomes are classified; disagreements are retained under
``benchmarks/differential/`` and never auto-resolved for a backend.

When ``MATHEVIDENCE_WOLFRAMSCRIPT`` is unset, Mathematica rows are labeled
``fixture`` / ``skip`` (CI-friendly) and may still compare SymPy live results
against committed Mathematica offline certificates when present.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.canonical import bind_request_digest  # noqa: E402
from adapters.common.errors import AdapterError  # noqa: E402
from adapters.common.lean_mirrors import check_rational_equality  # noqa: E402
from adapters.common.limits import ResourceLimits, ResourceTracker  # noqa: E402
from adapters.mathematica.adapter import (  # noqa: E402
    compute_rational_equality as mm_compute,
)
from adapters.mathematica.adapter import discover_runtime  # noqa: E402
from adapters.sympy.adapter import compute_rational_equality as sympy_compute  # noqa: E402

SUITE = ROOT / "evidence" / "conformance" / "rfc0001"
OUT_DIR = ROOT / "benchmarks" / "differential"
MANIFEST_PATH = OUT_DIR / "manifest.json"
DISAGREEMENTS_DIR = OUT_DIR / "disagreements"


@dataclass
class BackendOutcome:
    backend: str
    status: str  # live_ok | live_error | fixture | skip | offline_cert
    error_code: str | None = None
    message: str | None = None
    certificate: dict[str, Any] | None = None
    checker_accept: bool | None = None


def _load_cases() -> list[Path]:
    if not SUITE.is_dir():
        return []
    return sorted(p for p in SUITE.iterdir() if (p / "case.json").is_file())


def _load_request(case_dir: Path) -> dict[str, Any]:
    meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    request = json.loads((case_dir / "request.json").read_text(encoding="utf-8"))
    if meta.get("bindDigest", True) and meta.get("expect") != "digest_mismatch":
        request = bind_request_digest(request)
    return request


def _run_sympy(request: dict[str, Any]) -> BackendOutcome:
    tracker = ResourceTracker(ResourceLimits())
    try:
        result = sympy_compute(request, tracker)
        cert = result.result["certificate"]
        accept = check_rational_equality(request, cert)
        return BackendOutcome("sympy", "live_ok", certificate=cert, checker_accept=accept)
    except AdapterError as exc:
        return BackendOutcome(
            "sympy", "live_error", error_code=exc.code, message=exc.message
        )


def _committed_mm_cert(case_dir: Path) -> dict[str, Any] | None:
    path = case_dir / "bundle" / "certificate.json"
    if not path.is_file():
        return None
    cert = json.loads(path.read_text(encoding="utf-8"))
    if cert.get("provenance", {}).get("backendId") == "mathematica":
        return cert
    # Many rfc0001 bundles are SymPy-authored; still usable as offline reference
    # only when explicitly Mathematica. Prefer examples path for MM offline.
    return None


def _example_mm_cert_for_digest(digest: str) -> dict[str, Any] | None:
    """Match committed Mathematica offline example by request digest when present."""
    example = ROOT / "evidence" / "examples" / "rational_equality_mathematica_offline"
    req_path = example / "request.json"
    cert_path = example / "certificate.json"
    if not req_path.is_file() or not cert_path.is_file():
        return None
    req = json.loads(req_path.read_text(encoding="utf-8"))
    if req.get("requestDigest") == digest:
        return json.loads(cert_path.read_text(encoding="utf-8"))
    return None


def _run_mathematica(request: dict[str, Any], case_dir: Path) -> BackendOutcome:
    rt = discover_runtime()
    if rt.mode == "live" and rt.available and rt.executable:
        tracker = ResourceTracker(ResourceLimits())
        try:
            result = mm_compute(request, tracker, runtime=rt)
            cert = result.result["certificate"]
            accept = check_rational_equality(request, cert)
            return BackendOutcome(
                "mathematica", "live_ok", certificate=cert, checker_accept=accept
            )
        except AdapterError as exc:
            return BackendOutcome(
                "mathematica",
                "live_error",
                error_code=exc.code,
                message=exc.message,
            )

    # CI / no Wolfram: fixture or offline committed certificate when available.
    cert = _committed_mm_cert(case_dir) or _example_mm_cert_for_digest(
        str(request.get("requestDigest", ""))
    )
    if cert is not None:
        # Re-bind digest check against this request when digests match.
        if cert.get("requestDigest") == request.get("requestDigest"):
            accept = check_rational_equality(request, cert)
            return BackendOutcome(
                "mathematica",
                "fixture",
                message=rt.detail,
                certificate=cert,
                checker_accept=accept,
            )
    return BackendOutcome(
        "mathematica",
        "skip",
        message=rt.detail or "Mathematica unavailable; no matching offline certificate",
    )


def _classify(sym: BackendOutcome, mm: BackendOutcome) -> str:
    """Classify differential outcome; never resolve in favor of a backend."""
    if sym.status == "live_ok" and mm.status in {"live_ok", "fixture"}:
        if sym.checker_accept is True and mm.checker_accept is True:
            return "both_accepted"
        if sym.checker_accept is False and mm.checker_accept is False:
            return "both_checker_rejected"
        if sym.checker_accept != mm.checker_accept:
            return "semantic_disagreement"
        return "both_generated"
    if sym.status == "live_error" and mm.status in {"skip", "fixture"}:
        return "sympy_error_mm_unavailable"
    if mm.status == "skip":
        return "mathematica_skipped"
    if mm.status == "live_error" and mm.error_code == "backend_unsupported":
        return "one_unsupported"
    if sym.status == "live_error" and mm.status == "live_ok":
        return "one_error"
    if sym.status == "live_ok" and mm.status == "live_error":
        if mm.error_code in {"backend_unavailable", "backend_unsupported"}:
            return "one_unsupported"
        return "one_error"
    if sym.checker_accept is not None and mm.checker_accept is not None:
        if sym.checker_accept != mm.checker_accept:
            return "semantic_disagreement"
    return "recorded"


def _write_disagreement(case_id: str, row: dict[str, Any]) -> Path:
    DISAGREEMENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = DISAGREEMENTS_DIR / f"{case_id}.json"
    path.write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def run(*, write_manifest: bool = True) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = _load_cases()
    if not cases:
        print(f"missing differential suite source {SUITE}", file=sys.stderr)
        return 1

    rows: list[dict[str, Any]] = []
    disagreements = 0
    rt = discover_runtime()
    print(
        f"differential: mathematica mode={rt.mode} available={rt.available} "
        f"({rt.detail})"
    )

    for case_dir in cases:
        case_id = case_dir.name
        meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
        request = _load_request(case_dir)

        # Digest-mismatch / unsupported cases: still attempt classification.
        sym = _run_sympy(request)
        mm = _run_mathematica(request, case_dir)
        classification = _classify(sym, mm)

        row: dict[str, Any] = {
            "caseId": case_id,
            "expect": meta.get("expect"),
            "classification": classification,
            "requestDigest": request.get("requestDigest"),
            "sympy": {
                "status": sym.status,
                "errorCode": sym.error_code,
                "message": sym.message,
                "checkerAccept": sym.checker_accept,
            },
            "mathematica": {
                "status": mm.status,
                "errorCode": mm.error_code,
                "message": mm.message,
                "checkerAccept": mm.checker_accept,
            },
            "recordedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "autoResolved": False,
        }

        if classification == "semantic_disagreement":
            disagreements += 1
            path = _write_disagreement(case_id, row)
            row["disagreementPath"] = str(path.relative_to(ROOT)).replace("\\", "/")
            print(f"DISAGREEMENT {case_id} -> {row['disagreementPath']}")
        else:
            label = mm.status if mm.status in {"skip", "fixture"} else classification
            print(f"ok {case_id}: {classification} (mm={label})")

        rows.append(row)

    manifest = {
        "schemaVersion": "0.1.0",
        "suite": "evidence/conformance/rfc0001",
        "policy": "never_auto_resolve_disagreement",
        "mathematicaRuntime": {
            "mode": rt.mode,
            "available": rt.available,
            "detail": rt.detail,
        },
        "cases": rows,
        "disagreementCount": disagreements,
        "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if write_manifest:
        MANIFEST_PATH.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"wrote {MANIFEST_PATH.relative_to(ROOT)}")

    # Exit 0 even with skips/fixtures; fail only on semantic disagreement.
    if disagreements:
        print(
            f"differential FAILED: {disagreements} semantic disagreement(s) retained "
            f"(not auto-resolved)",
            file=sys.stderr,
        )
        return 1
    print(f"differential ok ({len(rows)} cases, mm mode={rt.mode})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Do not write benchmarks/differential/manifest.json",
    )
    args = parser.parse_args(argv)
    return run(write_manifest=not args.no_write)


if __name__ == "__main__":
    raise SystemExit(main())
