#!/usr/bin/env python3
"""Differential backend harness (TESTING_AND_CI.md §2.3).

Identical requests are sent to SymPy and Mathematica for:
- algebra.rational_equality (rfc0001)
- algebra.linear_algebra (accept cases)
- logic.finite_counterexample (accept cases)

Outcomes are classified; disagreements are retained under
``benchmarks/differential/`` and never auto-resolved for a backend.

When ``MATHEVIDENCE_WOLFRAMSCRIPT`` is unset, Mathematica rows are labeled
``fixture`` / ``skip`` (CI-friendly).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import find_role_path, load_role_json  # noqa: E402
from adapters.common.canonical import bind_request_digest  # noqa: E402
from adapters.common.errors import AdapterError  # noqa: E402
from adapters.common.lean_mirrors import (  # noqa: E402
    check_finite_counterexample,
    check_linear_algebra,
    check_rational_equality,
)
from adapters.common.limits import ResourceLimits, ResourceTracker  # noqa: E402
from adapters.mathematica.adapter import (  # noqa: E402
    compute_finite_counterexample as mm_cex,
)
from adapters.mathematica.adapter import (  # noqa: E402
    compute_linear_algebra as mm_la,
)
from adapters.mathematica.adapter import (  # noqa: E402
    compute_rational_equality as mm_rational,
)
from adapters.mathematica.adapter import discover_runtime  # noqa: E402
from adapters.sympy.adapter import (  # noqa: E402
    compute_finite_counterexample as sympy_cex,
)
from adapters.sympy.adapter import (  # noqa: E402
    compute_linear_algebra as sympy_la,
)
from adapters.sympy.adapter import (  # noqa: E402
    compute_rational_equality as sympy_rational,
)

OUT_DIR = ROOT / "benchmarks" / "differential"
MANIFEST_PATH = OUT_DIR / "manifest.json"
DISAGREEMENTS_DIR = OUT_DIR / "disagreements"

Checker = Callable[[dict[str, Any], dict[str, Any]], bool]
Compute = Callable[..., Any]


@dataclass
class BackendOutcome:
    backend: str
    status: str  # live_ok | live_error | fixture | skip | offline_cert
    error_code: str | None = None
    message: str | None = None
    certificate: dict[str, Any] | None = None
    checker_accept: bool | None = None


@dataclass(frozen=True)
class SuiteConfig:
    name: str
    root: Path
    capability: str
    sympy_compute: Compute
    mm_compute: Compute
    checker: Checker
    request_loader: Callable[[Path], dict[str, Any]]
    accept_only: bool = False


def _load_rfc_request(case_dir: Path) -> dict[str, Any]:
    meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    request = json.loads((case_dir / "request.json").read_text(encoding="utf-8"))
    if meta.get("bindDigest", True) and meta.get("expect") != "digest_mismatch":
        request = bind_request_digest(request)
    return request


def _load_bundle_request(case_dir: Path) -> dict[str, Any]:
    request = load_role_json(case_dir / "bundle", "request")
    return bind_request_digest(request)


def _suites() -> list[SuiteConfig]:
    return [
        SuiteConfig(
            name="rfc0001",
            root=ROOT / "evidence" / "conformance" / "rfc0001",
            capability="algebra.rational_equality",
            sympy_compute=sympy_rational,
            mm_compute=mm_rational,
            checker=check_rational_equality,
            request_loader=_load_rfc_request,
        ),
        SuiteConfig(
            name="linear_algebra",
            root=ROOT / "evidence" / "conformance" / "linear_algebra",
            capability="algebra.linear_algebra",
            sympy_compute=sympy_la,
            mm_compute=mm_la,
            checker=check_linear_algebra,
            request_loader=_load_bundle_request,
            accept_only=True,
        ),
        SuiteConfig(
            name="finite_counterexample",
            root=ROOT / "evidence" / "conformance" / "finite_counterexample",
            capability="logic.finite_counterexample",
            sympy_compute=sympy_cex,
            mm_compute=mm_cex,
            checker=check_finite_counterexample,
            request_loader=_load_bundle_request,
            accept_only=True,
        ),
    ]


def _case_dirs(suite: SuiteConfig) -> list[Path]:
    if not suite.root.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(suite.root.iterdir()):
        if not (p / "case.json").is_file():
            continue
        if suite.accept_only:
            meta = json.loads((p / "case.json").read_text(encoding="utf-8"))
            if meta.get("expect") != "accept":
                continue
            if find_role_path(p / "bundle", "request") is None:
                continue
        out.append(p)
    return out


def _run_backend(
    *,
    backend: str,
    compute: Compute,
    checker: Checker,
    request: dict[str, Any],
    live: bool,
    skip_detail: str,
) -> BackendOutcome:
    if not live:
        return BackendOutcome(backend, "skip", message=skip_detail)
    tracker = ResourceTracker(ResourceLimits())
    try:
        result = compute(request, tracker)
        cert = result.result["certificate"]
        accept = checker(request, cert)
        return BackendOutcome(backend, "live_ok", certificate=cert, checker_accept=accept)
    except AdapterError as exc:
        return BackendOutcome(
            backend, "live_error", error_code=exc.code, message=exc.message
        )


def _run_mathematica_rational_or_offline(
    request: dict[str, Any],
    case_dir: Path,
    suite: SuiteConfig,
    rt_detail: str,
    live: bool,
) -> BackendOutcome:
    if live:
        return _run_backend(
            backend="mathematica",
            compute=suite.mm_compute,
            checker=suite.checker,
            request=request,
            live=True,
            skip_detail=rt_detail,
        )

    # Rational suite: try committed Mathematica offline certificate.
    if suite.capability == "algebra.rational_equality":
        cert = _committed_mm_cert(case_dir) or _example_mm_cert_for_digest(
            str(request.get("requestDigest", ""))
        )
        if cert is not None and cert.get("requestDigest") == request.get("requestDigest"):
            accept = suite.checker(request, cert)
            return BackendOutcome(
                "mathematica",
                "fixture",
                message=rt_detail,
                certificate=cert,
                checker_accept=accept,
            )
    return BackendOutcome(
        "mathematica",
        "skip",
        message=rt_detail or "Mathematica unavailable; no matching offline certificate",
    )


def _committed_mm_cert(case_dir: Path) -> dict[str, Any] | None:
    path = find_role_path(case_dir / "bundle", "certificate")
    if path is None:
        return None
    cert = json.loads(path.read_text(encoding="utf-8"))
    if cert.get("provenance", {}).get("backendId") == "mathematica":
        return cert
    return None


def _example_mm_cert_for_digest(digest: str) -> dict[str, Any] | None:
    example = ROOT / "evidence" / "examples" / "rational_equality_mathematica_offline"
    req_path = find_role_path(example, "request")
    cert_path = find_role_path(example, "certificate")
    if req_path is None or cert_path is None:
        return None
    req = json.loads(req_path.read_text(encoding="utf-8"))
    if req.get("requestDigest") == digest:
        return json.loads(cert_path.read_text(encoding="utf-8"))
    return None


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
    suites = _suites()
    rows: list[dict[str, Any]] = []
    disagreements = 0
    rt = discover_runtime()
    live = bool(rt.mode == "live" and rt.available and rt.executable)
    print(
        f"differential: mathematica mode={rt.mode} available={rt.available} "
        f"({rt.detail})"
    )

    for suite in suites:
        cases = _case_dirs(suite)
        if not cases:
            print(f"skip suite {suite.name}: no cases under {suite.root}", file=sys.stderr)
            continue
        print(f"suite {suite.name} ({len(cases)} cases)")
        for case_dir in cases:
            case_id = f"{suite.name}/{case_dir.name}"
            meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
            request = suite.request_loader(case_dir)

            sym = _run_backend(
                backend="sympy",
                compute=suite.sympy_compute,
                checker=suite.checker,
                request=request,
                live=True,
                skip_detail="",
            )
            mm = _run_mathematica_rational_or_offline(
                request, case_dir, suite, rt.detail, live
            )
            classification = _classify(sym, mm)

            row: dict[str, Any] = {
                "caseId": case_id,
                "suite": suite.name,
                "capability": suite.capability,
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
                path = _write_disagreement(case_id.replace("/", "__"), row)
                row["disagreementPath"] = str(path.relative_to(ROOT)).replace("\\", "/")
                print(f"DISAGREEMENT {case_id} -> {row['disagreementPath']}")
            else:
                label = mm.status if mm.status in {"skip", "fixture"} else classification
                print(f"ok {case_id}: {classification} (mm={label})")

            rows.append(row)

    if not rows:
        print("differential: no cases loaded", file=sys.stderr)
        return 1

    manifest = {
        "schemaVersion": "0.1.0",
        "suites": [s.name for s in suites],
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
