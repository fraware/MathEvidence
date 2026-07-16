# Process isolation (adapter supervisors)

Normative companion to [SECURITY_AND_TRUST_MODEL.md](../SECURITY_AND_TRUST_MODEL.md) §5
and [TESTING_AND_CI.md](../TESTING_AND_CI.md) resource-limit layers.

## Documented limits

| Limit | Default | Source of truth | Enforcement |
| --- | --- | --- | --- |
| Wall time | 60 000 ms | Capability `limits.maxWallTimeMs` / request `resourcePolicy.maxWallTimeMs` | `ResourceTracker.check` (Python supervisor) |
| Output bytes | 4 194 304 | Capability / `resourcePolicy.maxOutputBytes` | Framing + tracker |
| Request bytes | 1 048 576 | `ResourceLimits.max_request_bytes` | NDJSON framing |
| JSON / IR nesting | 64 | `ResourceLimits.max_nesting_depth` / `expr_size` AST depth | `security_bounds` + `rational_ir.expr_size` |
| Integer digits | 4096 | Capability `limits.maxIntegerDigits` | `expr_size` / `security_bounds` |
| CPU time | 60 000 ms (advisory) | `resourcePolicy.maxCpuTimeMs` | Documented; OS cgroup when available |
| Memory | 512 MiB (advisory) | `resourcePolicy.maxMemoryBytes` | Documented; OS cgroup when available |

Python supervisors always enforce wall, output, request size, nesting, and
integer-digit bounds. CPU and memory caps are recorded on every compute request
and SHOULD be applied by the host (cgroup / Job Object) on production runners;
CI verifies cancel→kill so orphans cannot accumulate even when OS caps are soft.

## Cancel → kill

1. Client sends JSON-RPC `cancel` (sets in-flight `ResourceTracker.cancelled`).
2. Client calls `RpcClient.cancel_and_kill()` which terminates the adapter
   process and `kill()`s if still alive after a short grace period.
3. `RpcClient.close()` / context exit always waits then kills on timeout.

Tests: `adapters/common/test_isolation.py`.

## Working directory and paths

- Adapters spawn with a fixed argv (`default_adapter_argv`); no shell composition.
- Evidence bundle file paths must be workspace-relative without `..`
  (`reject_path_traversal` in `adapters/common/security_bounds.py`).
