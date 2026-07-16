#!/usr/bin/env python3
"""Run held-out Agent API benchmark tasks (in-process)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.api import service  # noqa: E402

MANIFEST = ROOT / "benchmarks" / "agent" / "held_out" / "manifest.json"


def _run_task(task: dict) -> tuple[bool, str]:
    op = task["operation"]
    inp = task.get("input", {})
    expect = task.get("expect", {})

    if op == "list_capabilities":
        out = service.op_list_capabilities()
        caps = out.get("capabilities", [])
        ids = {c["id"] for c in caps}
        need = expect.get("containsCapability")
        if need and need not in ids:
            return False, f"missing capability {need}"
        min_n = expect.get("minCapabilities")
        if isinstance(min_n, int) and len(caps) < min_n:
            return False, f"expected >= {min_n} capabilities, got {len(caps)}"
        return True, "ok"

    if op == "check_support":
        out = service.op_check_support(inp)
    elif op == "open_bundle":
        out = service.op_open_bundle(inp)
    elif op == "replay_bundle":
        out = service.op_replay_bundle(inp)
    elif op == "compute_evidence":
        out = service.op_compute_evidence(inp)
    else:
        return False, f"unknown operation {op}"

    if "resultStatus" in expect and out.get("resultStatus") != expect["resultStatus"]:
        return False, f"resultStatus {out.get('resultStatus')!r} != {expect['resultStatus']!r}"
    if "resultStatusIn" in expect and out.get("resultStatus") not in expect["resultStatusIn"]:
        return False, f"resultStatus {out.get('resultStatus')!r} not in {expect['resultStatusIn']}"
    if expect.get("hasBundleRef") and not out.get("bundleRef"):
        return False, "missing bundleRef"
    if "supported" in expect and out.get("supported") is not expect["supported"]:
        return False, f"supported={out.get('supported')}"
    needle = expect.get("notesContain")
    if needle:
        notes = " ".join(out.get("notes") or [])
        if needle not in notes:
            return False, f"notes missing {needle!r}"
    if "unresolvedObligations" not in out and op != "list_capabilities":
        return False, "missing unresolvedObligations"
    return True, "ok"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures = 0
    for rel in manifest["tasks"]:
        path = MANIFEST.parent / rel
        task = json.loads(path.read_text(encoding="utf-8"))
        ok, msg = _run_task(task)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {task['id']}: {msg}")
        if not ok:
            failures += 1
    if failures:
        print(f"agent held-out: {failures} failed", file=sys.stderr)
        return 1
    print(f"agent held-out ok ({len(manifest['tasks'])} tasks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
