# Federation agreements ledger

Records **real** maintainer agreements for live metadata emit/consume.
Engineering fixtures alone do **not** close Milestone 4 live exits.

| project_id | role | status | contact | agreed_at | notes |
| --- | --- | --- | --- | --- | --- |
| lean-smt | emitter | **OPEN** | — | — | Fixture emit only (`evidence/federation/examples/lean_smt_emit.json`) |
| cslib | consumer | **OPEN** | — | — | Fixture consume only (`evidence/federation/examples/cslib_consume.json`) |

Status values: `OPEN` | `proposed` | `agreed` | `live_smoke`.

Do not invent agreements. When a row moves to `agreed`, link the issue/PR and
enable optional `MATHEVIDENCE_FEDERATION_LIVE` smoke for that peer.
