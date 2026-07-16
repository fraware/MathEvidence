# Agent subsystem

Operation-level Agent API and Python SDK. No arbitrary shell execution.

## Layout

- `api/` — OpenAPI (`openapi.yaml`), JSON Schema I/O, thin HTTP server
- `sdk/` — typed Python client + CLI
- `hypothesis/` — Product 03 orchestration (lattice, deletion previews)
- `conjecture/` — Product 04 campaign helpers

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
| `compute_evidence` | Named adapter compute (`rational_equality`, `linear_algebra`, `finite_counterexample`, `symbolic_calculus`) |
| `open_bundle` | Epistemic status from bundle manifest |
| `replay_bundle` | Offline schema+digest replay |
| `propose_conditions` | Untrusted side-condition proposals |
| `prove_sufficient` | Sufficiency preview |
| `delete_hypothesis` | Deletion / redundancy preview |
| `find_counterexample` | Bounded CEX search |
| `verify_counterexample` | Python mirror of Lean Counterexample checker |
| `build_condition_lattice` | Condition lattice artifact |
| `conjecture_campaign` | Candidate vs certified refutation |

Results always include `resultStatus`, `unresolvedObligations`, and `bundleRef` where applicable.
