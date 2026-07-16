"""VS Code / Studio epistemic gate: Certified requires Lean status."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EPI = ROOT / "studio" / "vscode" / "epistemic.js"


def test_epistemic_certified_requires_lean() -> None:
    assert EPI.is_file()
    # Use absolute path; avoid cwd-relative require under pytest.
    epi_path = EPI.resolve().as_posix()
    script = f"""
const {{ epistemicFromResultStatus }} = require({epi_path!r});
const a = epistemicFromResultStatus('soundness_verified');
const b = epistemicFromResultStatus('soundness_verified', 'soundness_verified');
const c = epistemicFromResultStatus('computed');
if (a.label !== 'Ambiguous') {{ console.error(JSON.stringify(a)); process.exit(1); }}
if (b.label !== 'Certified') {{ console.error(JSON.stringify(b)); process.exit(2); }}
if (c.label !== 'Computed') {{ console.error(JSON.stringify(c)); process.exit(3); }}
console.log('ok');
"""
    proc = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "ok" in proc.stdout
