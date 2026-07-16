# MathEvidence Studio (Wolfram)

Human-facing Mathematica / Wolfram Language workflow for Product 09 (Milestone 5).
No unique mathematical semantics — Studio is a client of the Agent API, registry,
and Lean checkers.

## Install

```wolfram
AppendTo[$Path, FileNameJoin[{NotebookDirectory[], "..", "wolfram"}]];
(* or absolute path to studio/wolfram *)
Get["MathEvidenceStudio.wl"];
Needs["MathEvidenceStudio`"];
```

Optional Agent API:

```bash
just agent-api
```

Set `$MathEvidenceAgentBase` if not using `http://127.0.0.1:8787`.

## Epistemic states

| Label | When |
| --- | --- |
| Computed | Backend candidate only |
| Tested | Offline schema/digest OK; Lean not asserted |
| Certified | **Only** when Lean status is present **and** exact Lean proposition text is available |
| Ambiguous | Rejected / unsupported / missing / verified-without-Lean / Lean-without-proposition |

Color alone is insufficient; every badge includes text + detail
(`EpistemicFromResultStatus`, `StudioStateBadge`).

**Hard rule:** a manifest `resultStatus` of `soundness_verified` without
`$MathEvidenceLeanStatus` / `leanStatus` is shown as **Ambiguous**, never Certified.

**Surface rule:** `ShowLeanProposition` + `ShowAssumptions` always render
**before** the Certified affordance (`CertificationSurface` transcript order).

## Workflow (Product 09 §5)

1. Select / generate an expression (`ProposeCalculusRequest`).
2. Identify capability (`analysis.symbolic_calculus` or registry discovery).
3. Inspect exact proposed Lean statement and assumptions (`ShowLeanProposition`, `ShowAssumptions`).
4. Resolve ambiguities explicitly (domainConditions / ICs).
5. Backend generates candidate (SymPy / Mathematica adapter).
6. Lean checker runs (outside Studio TCB).
7. `CertifyInLean` displays established status + unresolved goals (after step 3 fields).
8. `ExportTheoremAndBundle` writes theorem + evidence.

## Principal actions

| Symbol | Role |
| --- | --- |
| `ProposeCalculusRequest` | Build calculus request skeleton |
| `ShowLeanProposition` | Exact proposed Lean statement (Agent/Lean field) |
| `ShowAssumptions` | Domain / singularity / IC display |
| `CertificationSurface` | Ordered transcript: proposition → assumptions → epistemic |
| `CertifyInLean` | Epistemic gate; Certified iff Lean status + proposition |
| `InspectBundle` | Open committed EvidenceBundle directory |
| `ExportTheoremAndBundle` | Export theorem text + bundle JSON |
| `ListStudioCapabilities` | Agent API discovery |

## LeanLink

LeanLink integration is scaffolded via the Mathematica adapter
(`MATHEVIDENCE_LEANLINK`). Studio does not embed checker semantics.

## Examples

See `Examples/CalculusWorkflow.wls`.

## Tests

```text
python -m pytest adapters/common/test_epistemic_studio.py -q
just studio-test
```

Golden transcripts: `studio/golden/transcripts/` (machine). Human usability:
`docs/validation/studio/usability/` (OPEN until sessions complete).

## Acceptance (Product 09)

- Users can distinguish Computed / Tested / Certified / Ambiguous (**human OPEN**).
- Exported theorems replay outside Mathematica (committed `evidence/`).
- Every backend-introduced condition is visible via `ShowAssumptions`.
- Exact Lean proposition / status available before certification labeling.
- UI uses only capability and orchestration APIs (no unique Studio math semantics).
