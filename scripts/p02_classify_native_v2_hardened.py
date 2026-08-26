#!/usr/bin/env python3
"""Post-adversarial hardened P02 native observation classifier (v2).

Classifier v2 is explicitly motivated by the frozen-v1 adversarial failures:
v1 scanned raw source text for policy tokens and therefore treated harmless
comments/string literals as policy violations. v2 changes *only* that policy
scan. Candidate/declaration/target process interpretation and decision order are
identical to frozen v1.

This file is post-hoc relative to the 13-case v1 adversarial development suite.
It must therefore be evaluated on a separately frozen holdout before any claim
of improved robustness is publication-eligible.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import p02_classify_native_v2_raw as v1

CLASSIFIER_VERSION = "p02_native_observation_classifier_v2_syntax_aware_policy"
DEVELOPMENT_SUITE_DIGEST = "sha256:b3db906353bdb5c53a732c2fd3f924ab445b116f58afbdac104c24d5334465c4"

# Policy tokens are searched only in code regions after comments, string
# literals, and guillemet-escaped identifiers are erased while preserving
# newlines. This is a deliberately small lexical layer, not a Lean parser.
_PLACEHOLDER_RE = re.compile(r"\b(sorry|admit)\b")
_AXIOM_RE = re.compile(r"(?m)^\s*(?:private\s+)?axiom\s+[A-Za-z_][A-Za-z0-9_']*")


def erase_noncode_regions(source: str) -> str:
    """Erase Lean comments, strings, and guillemet identifiers for policy scan.

    Newlines are preserved so beginning-of-line declaration checks remain
    meaningful. Lean block comments are nested. Backslash escapes inside string
    literals are consumed. This function intentionally does not attempt full
    parsing; holdout tests cover the policy-scanning invariants we rely on.
    """
    out: list[str] = []
    i = 0
    n = len(source)
    state = "code"
    block_depth = 0
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        if state == "code":
            if ch == "-" and nxt == "-":
                out.extend((" ", " "))
                i += 2
                state = "line_comment"
                continue
            if ch == "/" and nxt == "-":
                out.extend((" ", " "))
                i += 2
                state = "block_comment"
                block_depth = 1
                continue
            if ch == '"':
                out.append(" ")
                i += 1
                state = "string"
                continue
            if ch == "«":
                out.append(" ")
                i += 1
                state = "quoted_ident"
                continue
            out.append(ch)
            i += 1
            continue

        if state == "line_comment":
            if ch == "\n":
                out.append("\n")
                i += 1
                state = "code"
            else:
                out.append(" ")
                i += 1
            continue

        if state == "block_comment":
            if ch == "/" and nxt == "-":
                out.extend((" ", " "))
                i += 2
                block_depth += 1
                continue
            if ch == "-" and nxt == "/":
                out.extend((" ", " "))
                i += 2
                block_depth -= 1
                if block_depth == 0:
                    state = "code"
                continue
            out.append("\n" if ch == "\n" else " ")
            i += 1
            continue

        if state == "string":
            if ch == "\\" and i + 1 < n:
                out.append(" ")
                out.append("\n" if nxt == "\n" else " ")
                i += 2
                continue
            if ch == '"':
                out.append(" ")
                i += 1
                state = "code"
                continue
            out.append("\n" if ch == "\n" else " ")
            i += 1
            continue

        if state == "quoted_ident":
            if ch == "»":
                out.append(" ")
                i += 1
                state = "code"
            else:
                out.append("\n" if ch == "\n" else " ")
                i += 1
            continue

        raise AssertionError(state)

    # Unterminated source constructs will ordinarily be rejected by Lean before
    # policy scanning. Returning the erased prefix here keeps the scanner total.
    return "".join(out)


@dataclass(frozen=True)
class PolicyScan:
    has_placeholder: bool
    has_custom_axiom: bool
    sanitized_sha256: str

    @property
    def admissible(self) -> bool:
        return not self.has_placeholder and not self.has_custom_axiom


def scan_policy(source: str) -> PolicyScan:
    code = erase_noncode_regions(source)
    return PolicyScan(
        has_placeholder=_PLACEHOLDER_RE.search(code) is not None,
        has_custom_axiom=_AXIOM_RE.search(code) is not None,
        sanitized_sha256="sha256:" + hashlib.sha256(code.encode("utf-8")).hexdigest(),
    )


def self_test_policy_scanner() -> None:
    good = [
        "-- sorry\ntheorem t : True := by trivial\n",
        "/- axiom Ghost : True -/\ntheorem t : True := by trivial\n",
        "/- outer /- sorry -/ axiom Ghost : True -/\ntheorem t : True := by trivial\n",
        'def s : String := "sorry axiom Ghost"\ntheorem t : True := by trivial\n',
        "theorem «sorry» : True := by trivial\n",
    ]
    for source in good:
        scan = scan_policy(source)
        if not scan.admissible:
            raise AssertionError(f"policy scanner false positive on {source!r}: {scan}")

    bad = [
        "theorem t : True := by\n  sorry\n",
        "theorem t : True := by\n  admit\n",
        "axiom Ghost : True\ntheorem t : True := by trivial\n",
        "private axiom Ghost : True\ntheorem t : True := by trivial\n",
    ]
    for source in bad:
        scan = scan_policy(source)
        if scan.admissible:
            raise AssertionError(f"policy scanner false negative on {source!r}: {scan}")


def classify_case(case_dir: Path) -> dict[str, Any]:
    source = (case_dir / "candidate.lean").read_text(encoding="utf-8")
    raw = json.loads((case_dir / "observations.json").read_text(encoding="utf-8"))
    source_empty = not source.strip()
    if bool(raw.get("source_empty")) != source_empty:
        raise RuntimeError(f"source_empty mismatch for {case_dir.name}")
    candidate = v1.observation_from_json(raw.get("candidate"))
    if candidate is None:
        raise RuntimeError(f"missing candidate observation for {case_dir.name}")
    policy = scan_policy(source)
    observations = v1.NativeObservations(
        source_empty=source_empty,
        candidate=candidate,
        declaration_probe=v1.observation_from_json(raw.get("declaration_probe")),
        target_probe=v1.observation_from_json(raw.get("target_probe")),
        policy_has_placeholder=policy.has_placeholder,
        policy_has_custom_axiom=policy.has_custom_axiom,
    )
    derived = v1.derive_native_class(observations)
    if derived not in v1.NATIVE_CLASSES:
        raise AssertionError(f"invalid native class: {derived}")
    return {
        "case_id": raw.get("case_id") or case_dir.name,
        "derived_native_class": derived,
        "classifier_version": CLASSIFIER_VERSION,
        "parent_classifier_version": v1.CLASSIFIER_VERSION,
        "parent_frozen_classifier_blob_sha": v1.FROZEN_CLASSIFIER_BLOB_SHA,
        "policy_scan_version": "lean_lexical_noncode_erasure_v1",
        "policy_admissible": policy.admissible,
        "policy_has_placeholder": policy.has_placeholder,
        "policy_has_custom_axiom": policy.has_custom_axiom,
        "policy_sanitized_sha256": policy.sanitized_sha256,
        "source_sha256": v1.sha256_bytes(source.encode("utf-8")),
        "observations_sha256": v1.sha256_bytes((case_dir / "observations.json").read_bytes()),
    }


def classify_bundle(
    *,
    raw_root: Path,
    out_root: Path,
    expected_raw_digest: str,
    expected_n_cases: int,
    status: str,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    self_test_policy_scanner()
    v1.self_test_frozen_rules()
    if out_root.exists() and any(out_root.iterdir()):
        raise RuntimeError(f"v2 classification output not empty: {out_root}")
    out_root.mkdir(parents=True, exist_ok=True)

    integrity = json.loads((raw_root / "INTEGRITY_MANIFEST.json").read_text(encoding="utf-8"))
    files = v1.inventory(raw_root)
    if integrity.get("files") != files:
        raise RuntimeError("raw inventory mismatch")
    raw_digest = v1.canonical_digest({"files": files})
    if integrity.get("bundle_digest") != raw_digest or raw_digest != expected_raw_digest:
        raise RuntimeError(f"raw digest mismatch: {raw_digest} != {expected_raw_digest}")

    case_dirs = sorted(p for p in (raw_root / "cases").iterdir() if p.is_dir())
    if len(case_dirs) != expected_n_cases:
        raise RuntimeError(f"expected {expected_n_cases} cases, found {len(case_dirs)}")
    results = [classify_case(case_dir) for case_dir in case_dirs]
    counts = {name: 0 for name in sorted(v1.NATIVE_CLASSES)}
    for row in results:
        counts[row["derived_native_class"]] += 1
        v1.json_dump(out_root / "cases" / row["case_id"] / "classification.json", row)

    summary = {
        "schema_version": "p02_native_classification_v2_hardened",
        "status": status,
        "publication_claim_eligible": False,
        "classifier_version": CLASSIFIER_VERSION,
        "parent_classifier_version": v1.CLASSIFIER_VERSION,
        "parent_frozen_classifier_blob_sha": v1.FROZEN_CLASSIFIER_BLOB_SHA,
        "posthoc_relative_to_development_adversarial_suite": True,
        "development_adversarial_spec_digest": DEVELOPMENT_SUITE_DIGEST,
        "n_cases": len(results),
        "derived_class_counts": counts,
        "raw_bundle_digest": raw_digest,
        "expectation_metadata_read_during_classification": False,
        "only_policy_scan_changed_from_v1": True,
        "policy_scan_version": "lean_lexical_noncode_erasure_v1",
        "non_claims": [
            "v2 was motivated by frozen-v1 failures on the 13-case development adversarial suite.",
            "Performance on that development suite is not holdout evidence.",
            "Publication eligibility remains false until a separately frozen holdout suite is classified and audited.",
            "The scanner is lexical and does not claim to be a complete Lean parser."
        ],
    }
    if provenance:
        summary.update(provenance)
    v1.json_dump(out_root / "CLASSIFICATION_SUMMARY.json", summary)
    output_files = v1.inventory(out_root)
    out_integrity = {
        "schema_version": "p02_native_classification_v2_hardened_integrity",
        "publication_claim_eligible": False,
        "n_files": len(output_files),
        "files": output_files,
        "bundle_digest": v1.canonical_digest({"files": output_files}),
    }
    v1.json_dump(out_root / "INTEGRITY_MANIFEST.json", out_integrity)
    return {"summary": summary, "integrity": out_integrity}
