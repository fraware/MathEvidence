# Agent API changelog

All notable changes to the MathEvidence Agent API are recorded here.
The canonical protocol version is `info.version` in [`api/openapi.yaml`](api/openapi.yaml),
kept in sync with `PROTOCOL_VERSION` in `api/operations.py`.

## [0.1.0] — 2026-07-16

First versioned Agent API release (`agent-api-v0.1.0`).

### Spec

- OpenAPI 3.1 document at `agent/api/openapi.yaml` with `info.version: 0.1.0`
- Protocol constant `protocolVersion: "0.1.0"` on health and operation responses
- JSON Schema I/O under `agent/api/schemas/`

### Surface

- Operation-level HTTP API (no arbitrary shell or code execution)
- Capability discovery (`list_capabilities`, `check_support`)
- Evidence compute / open / replay for registered capabilities
- Hypothesis and conjecture orchestration endpoints
- Python SDK + CLI under `agent/sdk/`

### Release process

Engineering pins the OpenAPI version and this changelog in-tree.
Cutting the GitHub Release (annotated tag `agent-api-v0.1.0` + release notes that
point at `agent/api/openapi.yaml`) is a **human** step after the versioning
commit is pushed — see [`README.md`](README.md#release-notes-v010).
Do not invent external adoption claims in the release body.
