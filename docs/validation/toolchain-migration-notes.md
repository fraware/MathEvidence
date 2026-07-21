# Toolchain migration notes (ME-012)

**Current pin:** Lean `v4.14.0` / Mathlib `v4.14.0` (`lean-toolchain`, `lakefile.toml`).

## Done criterion for PR-Toolchain-Migration (this tree)

PR8 is **COMPLETE with BLOCKED bump** when all of the following hold:

1. Qualification checklist below is written and actionable.
2. Trust-repair scope on `v4.14.0` is explicitly cut-ready for `v0.1.1-trust-repair`
   (PRs 1–7 software path; no toolchain mix-in).
3. The bump itself is either (a) executed and green, or (b) recorded as **BLOCKED**
   with a concrete environment reason — not left as an open dangling todo.

**This working tree status:** **(b) BLOCKED** — keep `4.14.0`.

## Blocker (explicit)

| Factor | Detail |
| --- | --- |
| Merge discipline | Plan forbids combining toolchain migration with semantic/trust PRs already on the branch. |
| Network / TLS | Prior PyPI `UnknownIssuer` and long Mathlib fetch risk on this host; bump needs a clean `lake update` + full rebuild. |
| Scope | Semantic LA/CEX/analytic work must not share a half-migrated toolchain. |

## BLOCKED runbook — exact commands when TLS / network works

Do **not** half-migrate mid-capability. Execute on a dedicated branch only.

```powershell
# 0) Confirm TLS to PyPI / GitHub works (expect HTTP 200, not UnknownIssuer)
python -c "import urllib.request; print(urllib.request.urlopen('https://pypi.org/simple/pip/', timeout=30).status)"
git ls-remote https://github.com/leanprover-community/mathlib4.git HEAD

# 1) Dedicated branch from trust-repair green commit
git switch -c toolchain/current <trust-repair-green-sha>

# 2) Bump Lean + Mathlib together (edit lean-toolchain + lakefile.toml rev)
#    Then:
lake update
lake exe cache get   # if available for this toolchain

# 3) Full rebuild + gates
lake build
lake build mathevidence-replay mathevidence-axiom-report mathevidence-import-graph
python -m pytest tests/forensic -q
just check   # or the subset that does not require uv.lock yet

# 4) Python lock (only after PyPI TLS is clean)
uv lock
uv sync --frozen

# 5) Record axiom/perf delta vs v4.14.0 baseline, then immutable CI on the commit
```

If step 0 fails with `SSL: CERTIFICATE_VERIFY_FAILED` / `UnknownIssuer`: keep
`4.14.0`, use `requirements-freeze.txt`, and do not bump.

## Qualification checklist (when executing the bump on a dedicated branch)

1. Branch `toolchain/current` from a trust-repair green commit (`v0.1.1-trust-repair` candidate).
2. Bump `lean-toolchain` and Mathlib `rev` together to a current stable pair.
3. `lake update` / regenerate caches; repair API breakages without weakening proofs.
4. Rebuild: Core, IR, Checkers, Tactic (incl. LA/CEX examples), audit exes, offlineFixtures.
5. Re-run forensic suite + offline replay + focused LA/CEX/analytic builds.
6. Publish axiom/perf comparison vs `v4.14.0` baseline.
7. Tag only after immutable CI on the exact commit.

## `v0.1.1-trust-repair` readiness (trust-repair scope only)

On **Lean/Mathlib 4.14.0**, trust-repair software scope is prepared:

- Request binding, typed digests, theorem-producing rational replay, Agent sandbox,
  registry dispatch, compiled audit exes, CI pin / `just check`, freeze fallback for
  Python deps (`requirements-freeze.txt` when `uv.lock` blocked).

**Still required before claiming the release tag:** immutable CI green on the cut
commit + human branch-protection enablement (ME-407) — not asserted by this note.
