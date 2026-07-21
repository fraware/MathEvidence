# Agent subsystem

Operation-level Agent API and Python SDK. No arbitrary shell execution.

**Current release:** Agent API **v0.1.0** — see [Release notes (v0.1.0)](#release-notes-v010).

## Layout

- `api/` — OpenAPI (`openapi.yaml`), JSON Schema I/O, thin HTTP server
- `sdk/` — typed Python client + CLI
- `hypothesis/` — Product 03 orchestration (lattice, deletion previews)
- `conjecture/` — Product 04 campaign helpers
- [`CHANGELOG.md`](CHANGELOG.md) — versioned release history

## Run the API

```text
python -m agent.api.server --host 127.0.0.1 --port 8787
```

Health: `GET http://127.0.0.1:8787/v1/health`

## Hypothesis / conjecture flows (in-process)

```python
from agent.api import service

# Propose conditions + build lattice (minimality never claimed by default)
service.op_propose_conditions({"request": rational_request})
service.op_build_condition_lattice({"request": rational_request, "artifactId": "demo"})

# Conjecture campaign over a finite predicate family
service.op_conjecture_campaign({"request": finite_cex_request, "familyId": "finite.nat_le_3"})
```

HTTP paths:

- `POST /v1/hypothesis/propose-conditions`
- `POST /v1/hypothesis/prove-sufficient`
- `POST /v1/hypothesis/delete`
- `POST /v1/hypothesis/find-counterexample`
- `POST /v1/hypothesis/verify-counterexample`
- `POST /v1/hypothesis/build-lattice`
- `POST /v1/conjecture/campaign`

Pass `"captureEpisode": true` to write Foundry training episodes (never on the
acceptance path).

## Operations

| ID | Purpose |
| --- | --- |
| `list_capabilities` | Registry discovery |
| `check_support` | Pre-compute support gate |
| `compute_evidence` | Named adapter compute (`rational_equality`, `linear_algebra`, `finite_counterexample`, `symbolic_calculus` compute key; registry id `algebra.formal_rational_calculus`) |
| `open_bundle` | Epistemic status by opaque **`bundleId`** (raw paths rejected) |
| `replay_bundle` | Offline schema+digest replay by **`bundleId`** |
| `propose_conditions` | Untrusted side-condition proposals |
| `prove_sufficient` | Sufficiency preview |
| `delete_hypothesis` | Deletion / redundancy preview |
| `find_counterexample` | Bounded CEX search |
| `verify_counterexample` | Python mirror of Lean Counterexample checker |
| `build_condition_lattice` | Condition lattice artifact |
| `conjecture_campaign` | Candidate vs certified refutation |

Results always include `resultStatus`, `unresolvedObligations`, and `bundleRef` where applicable.

**Trust notes:** public open/inspect/replay reject raw filesystem paths. See
[`KNOWN_TRUST_GAPS.md`](../KNOWN_TRUST_GAPS.md) and [`docs/STATUS.md`](../docs/STATUS.md).
The Agent API remains experimental; no capability is stable.

## Release notes (v0.1.0)

| Field | Value |
| --- | --- |
| Protocol / OpenAPI version | `0.1.0` |
| Spec of record | [`agent/api/openapi.yaml`](api/openapi.yaml) (`info.version`) |
| Changelog | [`agent/CHANGELOG.md`](CHANGELOG.md) |
| Git tag (human-cut) | `agent-api-v0.1.0` |

v0.1.0 is the first **versioned** Agent API claim: the OpenAPI document and
`PROTOCOL_VERSION` are pinned at `0.1.0`, and the changelog names the release.
This does **not** claim external Lean-project adoption (that remains
`docs/validation/adoption-log.md`, human-owned).

### Cut the GitHub Release (after push)

After the versioning commit is on the remote branch, a maintainer cuts the
annotated tag and GitHub Release (do not invent adoption or stability claims
in the release body):

```text
git tag -a agent-api-v0.1.0 -m "Agent API v0.1.0

OpenAPI: agent/api/openapi.yaml (info.version 0.1.0)
Changelog: agent/CHANGELOG.md
"
git push origin agent-api-v0.1.0
gh release create agent-api-v0.1.0 --title "Agent API v0.1.0" --notes "Versioned Agent API release. Spec: agent/api/openapi.yaml (info.version 0.1.0). See agent/CHANGELOG.md."
```

Local annotated tag only (optional, before push): same `git tag -a` command
above; push when ready.
