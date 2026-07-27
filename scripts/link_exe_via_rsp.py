#!/usr/bin/env python3
"""Link a Lake Lean exe on Windows via a response file (ME-RV-022).

Lake 5 / Lean 4.14 invokes ``leanc`` with a full object list on the command
line. Windows ``CreateProcess`` rejects that with error 206 (command line too
long). Upstream Lake fixed this with ``@file.rsp`` response files after 4.14;
this helper reconstructs the failed link from a verbose Lake log (or a
captured arg list) and re-invokes ``leanc @rsp``.

Usage:
  python scripts/link_exe_via_rsp.py mathevidence-kernel-replay
  python scripts/link_exe_via_rsp.py mathevidence-kernel-replay --lake-log path.txt

Exit codes:
  0 — exe linked (or already present)
  2 — platform link still unavailable (structured: replay_dependency_missing)
  1 — unexpected failure
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEANC_RE = re.compile(
    r"leanc(?:\.exe)?\s+(-o\s+\S+\s+.+)$",
    re.IGNORECASE,
)


def _find_leanc() -> Path | None:
    import shutil

    # Prefer PATH / elan shim (reliable on Windows).
    found = shutil.which("leanc")
    if found:
        return Path(found)
    # Explicit toolchain fallback (Lean 4.14 pin).
    for cand in (
        Path.home()
        / ".elan"
        / "toolchains"
        / "leanprover--lean4---v4.14.0"
        / "bin"
        / ("leanc.exe" if os.name == "nt" else "leanc"),
    ):
        if cand.is_file():
            return cand
    return None


def _exe_candidates(name: str) -> list[Path]:
    bin_dir = ROOT / ".lake" / "build" / "bin"
    return [bin_dir / f"{name}.exe", bin_dir / name]


def _parse_leanc_args(log_text: str) -> list[str] | None:
    """Extract leanc argv (excluding the leanc binary) from a Lake -v log."""
    # Prefer the last leanc invocation; stop before the CreateProcess error line.
    lines = log_text.replace("\r\n", "\n").split("\n")
    leanc_line: str | None = None
    for line in lines:
        if re.search(r"leanc(?:\.exe)?\s+-o\s+", line, re.IGNORECASE):
            leanc_line = line
    if leanc_line is None:
        return None
    m = re.search(r"leanc(?:\.exe)?\s+(-o\s+.+)$", leanc_line, re.IGNORECASE)
    if m is None:
        return None
    tail = m.group(1).strip()
    # Tokenize; Lake prints unquoted paths with backslashes.
    args: list[str] = []
    buf: list[str] = []
    in_quote = False
    for ch in tail:
        if ch == '"':
            in_quote = not in_quote
            continue
        if ch == " " and not in_quote:
            if buf:
                args.append("".join(buf))
                buf = []
            continue
        buf.append(ch)
    if buf:
        args.append("".join(buf))
    # Normalize to forward slashes so clang @rsp does not eat `\`.
    normed = [a.replace("\\", "/") for a in args]
    return normed or None


def _run_lake_verbose(name: str) -> tuple[int, str]:
    log_path = ROOT / ".lake" / "build" / "bin" / f"{name}.lake-link.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", errors="replace", newline="\n") as fh:
        proc = subprocess.run(
            ["lake", "build", name, "-v"],
            stdout=fh,
            stderr=subprocess.STDOUT,
            cwd=str(ROOT),
            check=False,
            shell=False,
        )
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return proc.returncode, text


def link_via_rsp(name: str, *, lake_log: Path | None = None) -> int:
    for cand in _exe_candidates(name):
        if cand.is_file():
            print(f"link_exe_via_rsp: already present {cand}")
            return 0

    leanc = _find_leanc()
    if leanc is None:
        print(
            "replay_dependency_missing: leanc not found "
            "(cannot perform Windows rsp link)",
            file=sys.stderr,
        )
        return 2

    if lake_log is not None:
        log_text = lake_log.read_text(encoding="utf-8", errors="replace")
        lake_rc = 1
    else:
        print(f"link_exe_via_rsp: running lake build {name} -v …")
        lake_rc, log_text = _run_lake_verbose(name)
        for cand in _exe_candidates(name):
            if cand.is_file():
                print(f"link_exe_via_rsp: lake linked {cand}")
                return 0

    args = _parse_leanc_args(log_text)
    if args is None:
        print(
            "replay_dependency_missing: could not parse leanc argv from Lake log "
            f"(lake_rc={lake_rc}; Windows CreateProcess 206 is expected on 4.14)",
            file=sys.stderr,
        )
        return 2

    out_dir = ROOT / ".lake" / "build" / "bin"
    out_dir.mkdir(parents=True, exist_ok=True)
    rsp = out_dir / f"{name}.link.rsp"
    # clang/leanc response files: one argument per line, optionally quoted.
    # Match Lake's rsp escaping (lean4#7576): quote each arg; escape \ and ".
    def _escape(arg: str) -> str:
        out: list[str] = []
        for c in arg:
            if c in {'\\', '"'}:
                out.append("\\")
            out.append(c)
        return '"' + "".join(out) + '"'

    rsp.write_text("\n".join(_escape(a) for a in args) + "\n", encoding="utf-8", newline="\n")
    cmd = [str(leanc), f"@{rsp}"]
    print(f"link_exe_via_rsp: {leanc.name} @{rsp.name} ({len(args)} args)")
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
        shell=False,
    )
    if proc.returncode != 0:
        print(
            "replay_dependency_missing: leanc @rsp failed "
            f"rc={proc.returncode}\n{(proc.stderr or proc.stdout or '')[-2000:]}",
            file=sys.stderr,
        )
        return 2
    for cand in _exe_candidates(name):
        if cand.is_file():
            print(f"link_exe_via_rsp: linked {cand}")
            return 0
    print(
        "replay_dependency_missing: leanc @rsp returned 0 but exe missing",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("exe_name", help="Lake lean_exe name, e.g. mathevidence-kernel-replay")
    ap.add_argument(
        "--lake-log",
        type=Path,
        default=None,
        help="Optional pre-captured `lake build -v` log to parse",
    )
    ns = ap.parse_args()
    return link_via_rsp(ns.exe_name, lake_log=ns.lake_log)


if __name__ == "__main__":
    raise SystemExit(main())
