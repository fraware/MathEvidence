#!/usr/bin/env python3
"""Run held-out Agent API benchmark tasks (in-process).

Also compares MathEvidence pass rate vs a no-MathEvidence baseline that cannot
emit digest-bound evidence bundles or offline-replay them.
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

    if op == "compute_and_replay":
        scratch = Path(tempfile.mkdtemp(prefix="me_held_out_"))
        try:
            body = dict(inp)
            body["writeBundleTo"] = str(scratch)
            out = service.op_compute_evidence(body)
            if "resultStatus" in expect and out.get("resultStatus") != expect["resultStatus"]:
                return (
                    False,
                    f"compute resultStatus {out.get('resultStatus')!r} != "
                    f"{expect['resultStatus']!r}",
                )
            if expect.get("hasBundleRef") and not out.get("bundleRef"):
                return False, "missing bundleRef after compute"
            if "unresolvedObligations" not in out:
                return False, "missing unresolvedObligations after compute"
            replay = service.op_replay_bundle({"path": str(scratch)})
            want_replay = expect.get("replayResultStatus", "tested")
            if replay.get("resultStatus") != want_replay:
                return (
                    False,
                    f"replay resultStatus {replay.get('resultStatus')!r} != {want_replay!r}",
                )
            if "unresolvedObligations" not in replay:
                return False, "missing unresolvedObligations after replay"
            return True, "ok"
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

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


def _baseline_run_task(task: dict) -> tuple[bool, str]:
    """No-MathEvidence baseline: no registry, digests, bundles, or Lean-mirror replay."""
    op = task["operation"]
    if op in (
        "list_capabilities",
        "check_support",
        "open_bundle",
        "replay_bundle",
        "compute_and_replay",
        "compute_evidence",
    ):
        # Raw CAS may invent numbers, but cannot produce MathEvidence evidence protocol.
        return False, "baseline lacks MathEvidence registry/evidence protocol"
    return False, f"baseline unknown op {op}"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures = 0
    me_pass = 0
    base_pass = 0
    tasks = list(manifest["tasks"])
    for rel in tasks:
        path = MANIFEST.parent / rel
        task = json.loads(path.read_text(encoding="utf-8"))
        ok, msg = _run_task(task)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {task['id']}: {msg}")
        if ok:
            me_pass += 1
        else:
            failures += 1
        b_ok, b_msg = _baseline_run_task(task)
        print(f"  baseline {'PASS' if b_ok else 'FAIL'}: {b_msg}")
        if b_ok:
            base_pass += 1

    n = len(tasks)
    me_rate = me_pass / n if n else 0.0
    base_rate = base_pass / n if n else 0.0
    print(
        f"held-out rates: MathEvidence={me_pass}/{n} ({me_rate:.2%}) "
        f"baseline={base_pass}/{n} ({base_rate:.2%})"
    )
    if me_rate <= base_rate:
        print(
            "agent held-out: MathEvidence did not improve over no-MathEvidence baseline",
            file=sys.stderr,
        )
        return 1
    if failures:
        print(f"agent held-out: {failures} failed", file=sys.stderr)
        return 1
    print(f"agent held-out ok ({n} tasks; MathEvidence improves vs baseline)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
