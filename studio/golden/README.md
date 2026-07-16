# Golden epistemic transcripts (Product 09 / R6)

Machine-checkable cases for Studio Certified gating. These are **not**
human usability results.

Each file under `transcripts/` is a JSON object:

| Field | Meaning |
| --- | --- |
| `id` | Stable case id |
| `surface` | `vscode` / `wolfram` / `both` |
| `input` | `resultStatus`, optional `leanStatus`, `leanProposition`, `assumptions` / `request` |
| `expected.label` | Epistemic UI label after `buildCertificationSurface` |
| `expected.allowCertified` | Whether Certified affordance is allowed |
| `expected.transcriptOrder` | Must be proposition → assumptions → epistemic |

Run:

```text
python -m pytest adapters/common/test_epistemic_studio.py -q
# or
just studio-test
```
