# LeanLink / WXF fuzz stubs (native bridge disabled)

Committed binary-ish seeds for the scaffold fuzz harness in
`adapters/mathematica/leanlink_fuzz.py`. Public CI runs these via
`just leanlink-fuzz` / `security.yml`.

**Invariant:** nothing in this directory enables the native LeanLink bridge.
Blobs are classified and size-bounded only; they are not decoded by a C/WXF
runtime until `docs/architecture/leanlink-adapter-review.md` checkboxes close
with evidence.

| Seed | Intent |
| --- | --- |
| `empty.bin` | Empty input |
| `all_zero_64.bin` | Null padding |
| `truncated_wxf_header.bin` | Truncated fake WXF-like header bytes |
| `oversized_marker.txt` | Path/name marker; oversized case generated in-process |

Do not invent a “fuzz passed → enable LeanLink” claim from these stubs alone.
