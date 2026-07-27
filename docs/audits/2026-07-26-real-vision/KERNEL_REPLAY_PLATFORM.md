# Kernel-replay platform notes (ME-RV-022)

## Linux (CI authoritative)

`ubuntu-latest` in `.github/workflows/lean.yml` and `release.yml` builds and
links `mathevidence-kernel-replay`, then runs:

```text
lake build mathevidence-kernel-replay
.lake/build/bin/mathevidence-kernel-replay --self-test
.lake/build/bin/mathevidence-kernel-replay --self-test-analytic
```

asserting `soundness_verified` / `kernel_replay` for rational and analytic
product fixtures. CI sets `MATHEVIDENCE_REQUIRE_EXE_SMOKE=1` so a missing exe
is a hard fail. **Linux CI is the authoritative attestation** for the linked
kernel-replay executable.

## Windows (local) — rsp is the required path

Lake 5 on Lean **v4.14.0** may compile `MathEvidence.Exe.KernelReplay.olean`
while `leanc` fails to **link** with CreateProcess error **206** / **87**
(command line too long). Upstream Lake response-file (`@file.rsp`) support
landed after 4.14 (lean4#7576); this toolchain does not enable it automatically.

**Required local Windows workflow** (do not rely on bare `lake build` for the
exe):

```text
python scripts/link_exe_via_rsp.py mathevidence-kernel-replay
python scripts/smoke_exe.py
```

In-tree behavior:

1. **`scripts/link_exe_via_rsp.py mathevidence-kernel-replay`** — **required**
   Windows link helper: re-runs `lake build -v`, parses the failed `leanc`
   argv, writes `.lake/build/bin/mathevidence-kernel-replay.link.rsp`, and
   invokes `leanc @rsp`.
2. **`scripts/smoke_exe.py`** / **`just exe-smoke`** — on Windows, always
   attempt the rsp link before degrading; when the exe is present, run
   **both** `--self-test` and `--self-test-analytic`.
3. **Graceful degrade** — if rsp link still fails: exit 0 locally with
   structured `replay_dependency_missing` / `assurance_mode_unavailable`
   (olean presence proves fixture theorems compiled). Never emit Certified /
   `soundness_verified` without a successful exe self-test. Linked-exe
   attestation remains **Linux CI**.

Honest status:

- Olean success ⇒ `certified_rational_replay_basic_sympy` /
  `certified_analytic_replay_product_exe` / `replaySound` are kernel-accepted.
- Python `adapters.common.kernel_replay` still refuses Certified without a
  successful Lean compile of the generated module (or the fixture exe).
- Residual score: **PARTIAL(toolchain)** only — native Lake Windows link is
  not claimed MET. Do not claim Windows native Lake link MET; rsp path +
  Linux CI are the supported story.
