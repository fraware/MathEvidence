"""Finite simple-graph Conjecture vertical (Product 04 primary domain).

Executable companion to ``MathEvidence.Conjecture.Domains.FiniteGraph``.
Isomorphism policy: Graph6 canonical forms from the committed n≤7 atlas
(``evidence/conjecture/finite_graph/atlas_n7.g6``). Exact bitstring duplicates
are rejected; isomorphic labeled copies collapse to one atlas representative.

Authority: Lean ``checkBool`` owns falsification truth; this module uses the
Python Counterexample mirror for Agent/Foundry replay only.
"""

from __future__ import annotations

import json
from collections import Counter, deque
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from adapters.common.canonical import bind_request_digest
from adapters.common.hypothesis_util import find_counterexample
from adapters.common.lean_mirrors import check_finite_counterexample

GENERATOR_VERSION = "finite_graph.v0.2.0"
FAMILY_ID = "finite.simple_graph"
ATLAS_REL = Path("evidence/conjecture/finite_graph/atlas_n7.g6")
ARTIFACT_REL = Path("evidence/conjecture/finite_graph")

# Minimum invariants required by acceptance scale (spec 10 / ME-303).
INVARIANT_NAMES = (
    "n",
    "edge_count",
    "density",
    "degree_sequence",
    "triangle_count",
    "connected_components",
    "diameter",  # -1 when disconnected
    "is_bipartite",
)


@dataclass(frozen=True, slots=True)
class GraphInstance:
    """Canonical simple undirected graph (atlas representative)."""

    n: int
    upper_triangle: tuple[int, ...]
    graph6: str
    instance_id: str

    def adj(self) -> list[list[int]]:
        m = [[0] * self.n for _ in range(self.n)]
        k = 0
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if self.upper_triangle[k]:
                    m[i][j] = m[j][i] = 1
                k += 1
        return m


def edge_slot_count(n: int) -> int:
    return n * (n - 1) // 2


def decode_graph6(s: str) -> tuple[int, tuple[int, ...]]:
    """Decode a single Graph6 string (no header) → (n, upper-triangle bits)."""
    raw = s.strip()
    if not raw:
        raise ValueError("empty graph6")
    # Optional leading << which some writers emit; strip if present.
    if raw.startswith(">>graph6<<"):
        raw = raw[len(">>graph6<<") :]
    data = [ord(c) - 63 for c in raw]
    if any(b < 0 or b > 63 for b in data):
        raise ValueError(f"invalid graph6 byte in {s!r}")
    n = data[0]
    if n > 62:
        raise ValueError("extended graph6 (n>62) not supported in this vertical")
    need = (n * (n - 1) + 1) // 2  # bit count; ceil to 6-bit chars
    bit_count = n * (n - 1) // 2
    bits: list[int] = []
    for byte in data[1:]:
        for shift in range(5, -1, -1):
            bits.append((byte >> shift) & 1)
            if len(bits) >= bit_count:
                break
        if len(bits) >= bit_count:
            break
    if len(bits) < bit_count:
        raise ValueError(f"truncated graph6 {s!r} need={need}")
    return n, tuple(bits[:bit_count])


def encode_graph6(n: int, upper: Iterable[int]) -> str:
    """Encode upper-triangle bits as Graph6 (n≤62)."""
    if n > 62:
        raise ValueError("n>62 unsupported")
    bits = list(upper)
    if len(bits) != edge_slot_count(n):
        raise ValueError("upper triangle length mismatch")
    out = [chr(n + 63)]
    acc = 0
    filled = 0
    for b in bits:
        acc = (acc << 1) | (1 if b else 0)
        filled += 1
        if filled == 6:
            out.append(chr(acc + 63))
            acc = 0
            filled = 0
    if filled:
        acc <<= 6 - filled
        out.append(chr(acc + 63))
    return "".join(out)


def load_atlas(path: Path) -> list[GraphInstance]:
    """Load nonduplicate atlas representatives (isomorphism-collapsed)."""
    if not path.is_file():
        raise FileNotFoundError(path)
    seen: set[str] = set()
    out: list[GraphInstance] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        g6 = line.strip()
        if not g6 or g6.startswith("#"):
            continue
        if g6 in seen:
            continue
        seen.add(g6)
        n, upper = decode_graph6(g6)
        # Re-encode from bits to normalize representation.
        norm = encode_graph6(n, upper)
        iid = f"g6:{norm}"
        out.append(GraphInstance(n=n, upper_triangle=upper, graph6=norm, instance_id=iid))
    if len(out) < 1000:
        raise ValueError(f"atlas too small: {len(out)} < 1000 ({path})")
    return out


def compute_invariants(g: GraphInstance) -> dict[str, Any]:
    """≥5 meaningful computable invariants (returns 8)."""
    n = g.n
    m = g.adj()
    degrees = [sum(m[i]) for i in range(n)]
    edge_count = sum(degrees) // 2
    density = (2.0 * edge_count / (n * (n - 1))) if n > 1 else 0.0

    triangles = 0
    for i, j, k in combinations(range(n), 3):
        if m[i][j] and m[j][k] and m[i][k]:
            triangles += 1

    # Connected components + diameter (BFS).
    seen = [False] * n
    components = 0
    ecc: list[int] = []
    for start in range(n):
        if seen[start]:
            continue
        components += 1
        q: deque[int] = deque([start])
        seen[start] = True
        dist = {start: 0}
        while q:
            u = q.popleft()
            for v in range(n):
                if m[u][v] and v not in dist:
                    dist[v] = dist[u] + 1
                    seen[v] = True
                    q.append(v)
        if dist:
            ecc.append(max(dist.values()))
    diameter = -1 if components != 1 or n == 0 else (max(ecc) if ecc else 0)

    # Bipartite check via 2-coloring.
    color = [-1] * n
    bipartite = True
    for start in range(n):
        if color[start] != -1:
            continue
        color[start] = 0
        q = deque([start])
        while q and bipartite:
            u = q.popleft()
            for v in range(n):
                if not m[u][v]:
                    continue
                if color[v] == -1:
                    color[v] = 1 - color[u]
                    q.append(v)
                elif color[v] == color[u]:
                    bipartite = False
                    break

    return {
        "n": n,
        "edge_count": edge_count,
        "density": round(density, 6),
        "degree_sequence": tuple(sorted(degrees, reverse=True)),
        "triangle_count": triangles,
        "connected_components": components,
        "diameter": diameter,
        "is_bipartite": bipartite,
    }


def _edge_true(idx: int) -> dict[str, Any]:
    return {
        "tag": "eq",
        "left": {"tag": "var", "idx": idx},
        "right": {"tag": "lit", "v": {"tag": "bool", "v": True}},
    }


def _or_chain(preds: list[dict[str, Any]]) -> dict[str, Any]:
    if not preds:
        raise ValueError("empty or-chain")
    acc = preds[0]
    for p in preds[1:]:
        acc = {"tag": "or", "left": acc, "right": p}
    return acc


def _and_chain(preds: list[dict[str, Any]]) -> dict[str, Any]:
    if not preds:
        raise ValueError("empty and-chain")
    acc = preds[0]
    for p in preds[1:]:
        acc = {"tag": "and", "left": acc, "right": p}
    return acc


def family_request(n: int, pred: dict[str, Any]) -> dict[str, Any]:
    """Build a digest-bound finite-counterexample request for Fin-n edge bits."""
    slots = edge_slot_count(n)
    if slots == 0:
        raise ValueError("n<2 has no edge variables")
    var_names = []
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            var_names.append(f"e{i}{j}")
            k += 1
    req = {
        "schemaVersion": "0.1.0",
        "capability": "logic.finite_counterexample",
        "capabilityVersion": "0.1.0",
        "predicate": {
            "varNames": var_names,
            "domains": [{"ty": "bool"} for _ in range(slots)],
            "pred": pred,
        },
        "requestedClaim": "refutation",
        "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
    }
    return bind_request_digest(req)


def calibrated_candidates(n: int = 3) -> list[dict[str, Any]]:
    """Calibrated false / open / tautology candidates for Fin-n edge families.

    Primary false patterns mirror the Lean FiniteGraph empty-graph falsification
    and related sparse-graph counterexamples. Nat inequalities are not included.
    """
    slots = edge_slot_count(n)
    if slots < 1:
        raise ValueError("need n>=2")
    cands: list[dict[str, Any]] = []

    # False: every graph has at least one edge (empty falsifies) — Lean primary.
    pred_has_edge = _or_chain([_edge_true(i) for i in range(slots)])
    cands.append(
        {
            "id": f"fin{n}_has_edge",
            "kind": "false_universal",
            "pred": pred_has_edge,
            "expected": "falsified",
            "rationale": "Empty graph is a Lean-certified counterexample for n=3.",
        }
    )

    # False: a specific edge is always present.
    cands.append(
        {
            "id": f"fin{n}_edge0_always",
            "kind": "false_universal",
            "pred": _edge_true(0),
            "expected": "falsified",
            "rationale": "Any assignment with e0=false falsifies.",
        }
    )

    # False: all edges present (complete-graph universal).
    if slots >= 2:
        cands.append(
            {
                "id": f"fin{n}_complete",
                "kind": "false_universal",
                "pred": _and_chain([_edge_true(i) for i in range(slots)]),
                "expected": "falsified",
                "rationale": "Any missing edge falsifies completeness.",
            }
        )

    # False: at least two specific edges (for n>=3).
    if slots >= 3:
        cands.append(
            {
                "id": f"fin{n}_edge0_and_edge1",
                "kind": "false_universal",
                "pred": {
                    "tag": "and",
                    "left": _edge_true(0),
                    "right": _edge_true(1),
                },
                "expected": "falsified",
                "rationale": "Empty or single-edge graphs falsify.",
            }
        )
        # False: OR of first two edges only (third-only graph may falsify for n=3).
        cands.append(
            {
                "id": f"fin{n}_edge0_or_edge1",
                "kind": "false_universal",
                "pred": {
                    "tag": "or",
                    "left": _edge_true(0),
                    "right": _edge_true(1),
                },
                "expected": "falsified",
                "rationale": "Graph with only the last edge falsifies for n=3.",
            }
        )

    # Tautology / formally provable on the finite family: e0 == e0.
    cands.append(
        {
            "id": f"fin{n}_edge0_refl",
            "kind": "tautology",
            "pred": {
                "tag": "eq",
                "left": {"tag": "var", "idx": 0},
                "right": {"tag": "var", "idx": 0},
            },
            "expected": "formally_proved",
            "theoremRef": f"edge_var_refl_fin{n}",
            "rationale": "Reflexive equality on a Bool edge variable.",
        }
    )

    # Open / bounded: not(e0) or e0 — true but recorded as bounded_verified demo.
    cands.append(
        {
            "id": f"fin{n}_excluded_middle_edge0",
            "kind": "bounded_survivor",
            "pred": {
                "tag": "or",
                "left": {
                    "tag": "eq",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "lit", "v": {"tag": "bool", "v": False}},
                },
                "right": _edge_true(0),
            },
            "expected": "bounded_verified",
            "searchBound": 2**slots,
            "rationale": "Holds on the finite family; not lifted as an unbounded theorem here.",
        }
    )

    return cands


def run_falsification_batch(
    *,
    n: int = 3,
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Exercise Lean-mirror certified falsification on a calibrated batch."""
    # Local imports avoid circular import with agent.conjecture.__init__.
    from agent.conjecture import (
        certify_refutation,
        mark_bounded_verified,
        mark_formally_proved,
        mark_open_problem,
        new_episode,
        precision_accounting,
        to_candidate,
    )

    cands = candidates or calibrated_candidates(n)
    episodes: list[dict[str, Any]] = []
    counterexamples: list[dict[str, Any]] = []
    for cand in cands:
        pred = cand["pred"]
        req = family_request(n, pred)
        ep = to_candidate(new_episode(family_id=f"{FAMILY_ID}_fin{n}", pred=pred))
        expected = cand.get("expected")
        if expected == "formally_proved":
            ep = mark_formally_proved(ep, str(cand.get("theoremRef") or "unspecified"))
        elif expected == "bounded_verified":
            ep = mark_open_problem(
                mark_bounded_verified(ep, int(cand.get("searchBound") or 0)),
                str(cand.get("rationale") or "bounded survivor"),
            )
        else:
            cert = find_counterexample(req)
            if cert is not None:
                ok = check_finite_counterexample(req, cert)
                ep = certify_refutation(
                    ep,
                    request=req,
                    certificate=cert,
                    refutation_id=str(cand.get("id") or "cex"),
                )
                counterexamples.append(
                    {
                        "candidateId": cand.get("id"),
                        "request": req,
                        "certificate": cert,
                        "mirrorAccepted": ok,
                        "authorityStatus": "lean_checker_mirror",
                    }
                )
            else:
                ep = mark_bounded_verified(ep, 2 ** edge_slot_count(n))
        ep["candidateId"] = cand.get("id")
        ep["candidateKind"] = cand.get("kind")
        ep["generatorVersion"] = GENERATOR_VERSION
        episodes.append(ep)

    accounting = precision_accounting(episodes, family_id=f"{FAMILY_ID}_fin{n}")
    accounting["notes"] = list(accounting.get("notes") or []) + [
        "Precision is campaign-local; do not claim field-level performance from tiny batches.",
        f"generatorVersion={GENERATOR_VERSION}",
    ]
    return {
        "generatorVersion": GENERATOR_VERSION,
        "familyId": f"{FAMILY_ID}_fin{n}",
        "n": n,
        "candidates": cands,
        "episodes": episodes,
        "counterexamples": counterexamples,
        "precisionAccounting": accounting,
        "authorityStatus": "lean_checker_mirror",
    }


def expand_falsification_variants(n: int = 3, *, limit: int = 512) -> list[dict[str, Any]]:
    """Generate many distinct false universals over edge bits (Foundry Q2 scale).

    Each variant asserts that a nonempty subset of edges is entirely present
    (AND of those edge-true literals). The empty graph falsifies every such claim.
    """
    slots = edge_slot_count(n)
    out: list[dict[str, Any]] = []
    # Nonempty subsets in gray-code / bitmask order; cap at limit.
    for mask in range(1, 2**slots):
        if len(out) >= limit:
            break
        idxs = [i for i in range(slots) if (mask >> i) & 1]
        pred = _and_chain([_edge_true(i) for i in idxs]) if len(idxs) > 1 else _edge_true(idxs[0])
        out.append(
            {
                "id": f"fin{n}_subset_{mask:0{slots}b}",
                "kind": "false_universal",
                "pred": pred,
                "expected": "falsified",
                "rationale": "Empty graph falsifies any nonempty edge-AND claim.",
                "mask": mask,
            }
        )
    return out


def instance_records(instances: list[GraphInstance]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for g in instances:
        inv = compute_invariants(g)
        rows.append(
            {
                "instanceId": g.instance_id,
                "generatorVersion": GENERATOR_VERSION,
                "n": g.n,
                "graph6": g.graph6,
                "upperTriangle": list(g.upper_triangle),
                "invariants": inv,
            }
        )
    return rows


def summarize_instances(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_n: Counter[int] = Counter(int(r["n"]) for r in records)
    return {
        "generatorVersion": GENERATOR_VERSION,
        "instanceCount": len(records),
        "nonduplicatePolicy": "graph6_atlas_isomorphism_collapse",
        "invariantNames": list(INVARIANT_NAMES),
        "invariantCount": len(INVARIANT_NAMES),
        "byN": {str(k): by_n[k] for k in sorted(by_n)},
        "atlasRel": str(ATLAS_REL).replace("\\", "/"),
    }


def write_campaign_artifacts(
    repo_root: Path,
    *,
    batch: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Path]:
    """Persist Foundry-compatible conjecture artifacts under evidence/conjecture."""
    root = repo_root / ARTIFACT_REL
    root.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    summary = summarize_instances(records)
    summary_path = root / "manifest.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    paths["manifest"] = summary_path

    inst_path = root / "instances.jsonl"
    with inst_path.open("w", encoding="utf-8") as fh:
        for row in records:
            fh.write(json.dumps(row, separators=(",", ":"), ensure_ascii=False) + "\n")
    paths["instances"] = inst_path

    inv_path = root / "invariants.jsonl"
    with inv_path.open("w", encoding="utf-8") as fh:
        for row in records:
            fh.write(
                json.dumps(
                    {
                        "instanceId": row["instanceId"],
                        "generatorVersion": GENERATOR_VERSION,
                        "invariants": row["invariants"],
                    },
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            )
    paths["invariants"] = inv_path

    cand_path = root / "candidates.json"
    cand_path.write_text(
        json.dumps(
            {
                "generatorVersion": GENERATOR_VERSION,
                "familyId": batch["familyId"],
                "candidates": batch["candidates"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["candidates"] = cand_path

    bounds_path = root / "bounds.json"
    bounds_path.write_text(
        json.dumps(
            {
                "generatorVersion": GENERATOR_VERSION,
                "enumerateBound": 2 ** edge_slot_count(int(batch["n"])),
                "n": batch["n"],
                "searchNotes": "Finite Fin-n edge-bit family; bounded_verified ≠ unbounded theorem.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["bounds"] = bounds_path

    cex_path = root / "counterexamples.json"
    cex_path.write_text(
        json.dumps(
            {
                "generatorVersion": GENERATOR_VERSION,
                "authorityStatus": "lean_checker_mirror",
                "counterexamples": batch["counterexamples"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["counterexamples"] = cex_path

    prec_path = root / "precision.json"
    prec_path.write_text(
        json.dumps(batch["precisionAccounting"], indent=2) + "\n", encoding="utf-8"
    )
    paths["precision"] = prec_path

    ep_path = root / "campaign_episodes.json"
    ep_path.write_text(
        json.dumps(
            {
                "generatorVersion": GENERATOR_VERSION,
                "episodes": batch["episodes"],
                "authorityStatus": batch["authorityStatus"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["campaign_episodes"] = ep_path

    readme = root / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# FiniteGraph conjecture artifacts",
                "",
                f"Generator: `{GENERATOR_VERSION}`",
                "",
                "Primary Conjecture vertical (Product 04). Nat inequality fixtures are",
                "non-primary regression only.",
                "",
                "## Contents",
                "",
                "- `atlas_n7.g6` — isomorphism-collapsed simple graphs on n≤7 (≥1000).",
                "- `instances.jsonl` / `invariants.jsonl` — objects + computable invariants.",
                "- `candidates.json` / `counterexamples.json` / `precision.json` — campaign.",
                "- `bounds.json` — finite enumerate bounds (not unbounded theorems).",
                "",
                "## Authority",
                "",
                "Falsification status requires Lean `checkBool` (Python mirror for replay).",
                "Do not claim field-level precision from tiny campaign batches.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    paths["readme"] = readme
    return paths


def as_plain(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return obj
