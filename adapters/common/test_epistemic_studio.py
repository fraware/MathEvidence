"""Studio Product 09 epistemic gate — integration + golden transcripts.

Covers VS Code (Node epistemic.js) and the shared Python contract that mirrors
Wolfram MathEvidenceStudio`CertificationSurface` / EpistemicFromResultStatus.

Does not invent human usability results.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EPI_JS = ROOT / "studio" / "vscode" / "epistemic.js"
GOLDEN_DIR = ROOT / "studio" / "golden" / "transcripts"
CONTRACT = ROOT / "studio" / "epistemic_contract.py"

sys.path.insert(0, str(ROOT))
from studio.epistemic_contract import (  # noqa: E402
    build_certification_surface,
    epistemic_from_result_status,
    lean_status_allows_certified,
)


def _load_goldens() -> list[dict]:
    assert GOLDEN_DIR.is_dir(), f"missing golden dir: {GOLDEN_DIR}"
    cases = []
    for path in sorted(GOLDEN_DIR.glob("*.json")):
        cases.append(json.loads(path.read_text(encoding="utf-8")))
    assert len(cases) >= 3, "expected ≥3 golden transcripts"
    return cases


def _run_node_surface(case_input: dict) -> dict:
    payload = json.dumps(
        {
            "resultStatus": case_input.get("resultStatus"),
            "leanStatus": case_input.get("leanStatus"),
            "leanProposition": case_input.get("leanProposition"),
            "assumptions": case_input.get("assumptions"),
            "request": case_input.get("request"),
            "manifest": case_input.get("manifest"),
            "theoremPreview": case_input.get("theoremPreview"),
        }
    )
    epi_path = EPI_JS.resolve().as_posix()
    script = f"""
const {{ buildCertificationSurface, epistemicFromResultStatus }} = require({epi_path!r});
const input = {payload};
const surface = buildCertificationSurface(input);
const gate = epistemicFromResultStatus(input.resultStatus, input.leanStatus);
process.stdout.write(JSON.stringify({{ surface, gate }}));
"""
    proc = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(proc.stdout)


def test_epistemic_js_module_exists() -> None:
    assert EPI_JS.is_file()
    assert CONTRACT.is_file()


def test_epistemic_certified_requires_lean_gate_only() -> None:
    """Hard rule: epistemicFromResultStatus Certified ⇔ Lean status."""
    a = epistemic_from_result_status("soundness_verified")
    b = epistemic_from_result_status("soundness_verified", "soundness_verified")
    c = epistemic_from_result_status("computed")
    assert a["label"] == "Ambiguous" and not a["allowCertified"]
    assert b["label"] == "Certified" and b["allowCertified"]
    assert c["label"] == "Computed" and not c["allowCertified"]
    assert lean_status_allows_certified("witness_verified")
    assert not lean_status_allows_certified("")
    assert not lean_status_allows_certified(None)


def test_node_parity_certified_requires_lean() -> None:
    assert EPI_JS.is_file()
    epi_path = EPI_JS.resolve().as_posix()
    script = f"""
const {{ epistemicFromResultStatus }} = require({epi_path!r});
const a = epistemicFromResultStatus('soundness_verified');
const b = epistemicFromResultStatus('soundness_verified', 'soundness_verified');
const c = epistemicFromResultStatus('computed');
if (a.label !== 'Ambiguous' || a.allowCertified) {{ console.error(JSON.stringify(a)); process.exit(1); }}
if (b.label !== 'Certified' || !b.allowCertified) {{ console.error(JSON.stringify(b)); process.exit(2); }}
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


@pytest.mark.parametrize("case", _load_goldens(), ids=lambda c: c["id"])
def test_golden_python_surface(case: dict) -> None:
    inp = case["input"]
    exp = case["expected"]
    surface = build_certification_surface(
        result_status=inp.get("resultStatus"),
        lean_status=inp.get("leanStatus"),
        lean_proposition=inp.get("leanProposition"),
        theorem_preview=inp.get("theoremPreview"),
        request=inp.get("request"),
        manifest=inp.get("manifest"),
        assumptions=inp.get("assumptions"),
    )
    assert surface["transcriptOrder"] == exp["transcriptOrder"]
    assert surface["epistemic"]["label"] == exp["label"]
    assert surface["epistemic"]["allowCertified"] is exp["allowCertified"]
    # Proposition and assumptions sections precede Certified affordance.
    assert surface["transcriptOrder"].index("leanProposition") < surface[
        "transcriptOrder"
    ].index("epistemicLabel")
    assert surface["transcriptOrder"].index("assumptions") < surface[
        "transcriptOrder"
    ].index("epistemicLabel")
    assert surface["certifiedAffordanceIndex"] == surface["transcriptOrder"].index(
        "epistemicLabel"
    )


@pytest.mark.parametrize("case", _load_goldens(), ids=lambda c: c["id"])
def test_golden_node_surface_parity(case: dict) -> None:
    inp = case["input"]
    exp = case["expected"]
    out = _run_node_surface(inp)
    surface = out["surface"]
    assert surface["transcriptOrder"] == exp["transcriptOrder"]
    assert surface["epistemic"]["label"] == exp["label"]
    assert surface["epistemic"]["allowCertified"] is exp["allowCertified"]


def test_python_node_label_parity_matrix() -> None:
    pairs = [
        ("computed", None),
        ("tested", None),
        ("soundness_verified", None),
        ("soundness_verified", "soundness_verified"),
        ("witness_verified", "witness_verified"),
        ("ambiguous", None),
        ("rejected", ""),
    ]
    for result_status, lean_status in pairs:
        py = epistemic_from_result_status(result_status, lean_status)
        out = _run_node_surface(
            {
                "resultStatus": result_status,
                "leanStatus": lean_status,
                "leanProposition": "theorem placeholder : True := trivial",
                "assumptions": [],
            }
        )
        gate = out["gate"]
        assert gate["label"] == py["label"], (result_status, lean_status)
        assert gate["allowCertified"] is py["allowCertified"]


def test_wolfram_package_documents_certified_gate() -> None:
    """Wolfram surface ships the same Certified-iff-Lean contract (no Mathematica required)."""
    wl = (ROOT / "studio" / "wolfram" / "MathEvidenceStudio.wl").read_text(
        encoding="utf-8"
    )
    assert "AllowCertified" in wl
    assert "never present Certified without" in wl or "never labels Certified without" in wl
    assert "CertificationSurface" in wl
    assert "ShowLeanProposition" in wl
    assert '"leanProposition"' in wl or "leanProposition" in wl
    # Transcript order encoded in WL.
    assert "leanProposition" in wl and "assumptions" in wl and "epistemicLabel" in wl
    epi_md = (ROOT / "studio" / "wolfram" / "EPISTEMIC.md").read_text(encoding="utf-8")
    assert "AllowCertified" in epi_md
    assert "proposition" in epi_md.lower()


def test_vscode_panel_orders_proposition_before_certified() -> None:
    ext = (ROOT / "studio" / "vscode" / "extension.js").read_text(encoding="utf-8")
    prop_idx = ext.index('data-section="leanProposition"')
    assumps_idx = ext.index('data-section="assumptions"')
    epi_idx = ext.index('data-section="epistemicLabel"')
    assert prop_idx < assumps_idx < epi_idx
    assert "buildCertificationSurface" in ext


def test_no_unique_semantics_claim_in_studio_readme() -> None:
    readme = (ROOT / "studio" / "README.md").read_text(encoding="utf-8")
    assert "No unique mathematical semantics" in readme
