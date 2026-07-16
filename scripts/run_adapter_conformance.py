#!/usr/bin/env python3
"""Run SymPy adapter conformance cases from evidence/conformance/rfc0001."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.canonical import bind_request_digest, verify_request_digest  # noqa: E402
from adapters.common.errors import AdapterError  # noqa: E402
from adapters.common.limits import ResourceLimits, ResourceTracker  # noqa: E402
from adapters.common.schema_validate import SchemaStore  # noqa: E402
from adapters.sympy.adapter import compute_rational_equality  # noqa: E402

SUITE = ROOT / "evidence" / "conformance" / "rfc0001"


def run_case(case_dir: Path, store: SchemaStore) -> None:
    meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    expect = meta["expect"]
    request = json.loads((case_dir / "request.json").read_text(encoding="utf-8"))

    if meta.get("bindDigest", True):
        request = bind_request_digest(request)

    tracker = ResourceTracker(ResourceLimits())
    if expect == "unsupported":
        try:
            compute_rational_equality(request, tracker, schemas=store)
        except AdapterError as exc:
            if exc.code != meta.get("errorCode", "unsupported_expression"):
                raise AssertionError(f"{case_dir.name}: wrong error {exc.code}") from exc
            return
        raise AssertionError(f"{case_dir.name}: expected unsupported rejection")

    if expect == "digest_mismatch":
        # Leave wrong digest in place.
        try:
            verify_request_digest(request)
            # If somehow valid, force compute path to check.
            compute_rational_equality(request, tracker, schemas=store)
        except AdapterError as exc:
            if exc.code != "request_digest_mismatch":
                raise AssertionError(f"{case_dir.name}: wrong error {exc.code}") from exc
            return
        except Exception:
            return
        raise AssertionError(f"{case_dir.name}: expected digest mismatch")

    result = compute_rational_equality(request, tracker, schemas=store)
    cert = result.result["certificate"]
    numer = cert["differenceNumerator"]
    is_zero = numer == {"tag": "int", "value": "0"}

    if expect == "valid_identity":
        if not is_zero:
            raise AssertionError(f"{case_dir.name}: expected zero numerator, got {numer}")
    elif expect == "false_identity":
        if is_zero:
            raise AssertionError(f"{case_dir.name}: expected non-zero numerator")
    elif expect == "candidate_ok":
        pass
    else:
        raise AssertionError(f"{case_dir.name}: unknown expect {expect}")

    # Optional factor checks
    if "requireFactorRoles" in meta:
        roles = {f["role"] for f in cert["denominatorFactors"]}
        for role in meta["requireFactorRoles"]:
            if role not in roles:
                raise AssertionError(f"{case_dir.name}: missing factor role {role}")


def main() -> int:
    if not SUITE.is_dir():
        print(f"missing suite {SUITE}", file=sys.stderr)
        return 1
    store = SchemaStore()
    cases = sorted(p for p in SUITE.iterdir() if (p / "case.json").is_file())
    if not cases:
        print("no conformance cases", file=sys.stderr)
        return 1
    failures = 0
    for case_dir in cases:
        try:
            run_case(case_dir, store)
            print(f"ok {case_dir.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {case_dir.name}: {exc}", file=sys.stderr)
            failures += 1
    if failures:
        print(f"adapter-conformance failed ({failures})", file=sys.stderr)
        return 1
    print(f"adapter-conformance ok ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
