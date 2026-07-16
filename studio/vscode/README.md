# MathEvidence VS Code Evidence Inspector

Partial Product 09 surface (Milestone 2). Wolfram Studio is deferred to Milestone 5.

## Features

- **Epistemic states** (text + color): Computed, Tested, Certified, Ambiguous
- **Open Evidence Bundle** folder (`manifest.json` + digests)
- **Replay link** (`mathevidence://replay?path=…`) via command that runs offline Python digest/schema checks through the Agent SDK

No unique mathematical semantics live in this extension; it is a client of committed bundles and the Agent API.

## Run / install (development)

From the repo root:

```text
code --extensionDevelopmentPath=studio/vscode
```

Or in VS Code: **Extensions: Install from Location…** → select `studio/vscode`.

Commands:

- `MathEvidence: Open Evidence Bundle`
- `MathEvidence: Replay Evidence Bundle (link)`
- `MathEvidence: Show Epistemic States`

Optional settings:

- `mathevidence.pythonPath` — Python used for local replay (`python -m agent.sdk --local replay-bundle …`)
- `mathevidence.agentApiBaseUrl` — reserved for HTTP Agent API clients

## Smoke test

```text
node -e "console.log(require('./epistemic').epistemicFromResultStatus('computed'))"
```

(Full `extension.js` loads only inside VS Code, which provides the `vscode` module.)