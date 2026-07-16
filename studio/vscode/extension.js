"use strict";

const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const { epistemicFromResultStatus } = require("./epistemic");

/**
 * @param {string} bundleDir
 */
function loadManifest(bundleDir) {
  const manifestPath = path.join(bundleDir, "manifest.json");
  if (!fs.existsSync(manifestPath)) {
    throw new Error(`Missing manifest.json in ${bundleDir}`);
  }
  return JSON.parse(fs.readFileSync(manifestPath, "utf8"));
}

/**
 * @param {vscode.ExtensionContext} context
 * @param {string} bundleDir
 * @param {object} manifest
 * @param {{ label: EpistemicLabel, detail: string }} epistemic
 */
function showBundlePanel(context, bundleDir, manifest, epistemic) {
  const panel = vscode.window.createWebviewPanel(
    "mathevidenceBundle",
    `Evidence: ${path.basename(bundleDir)}`,
    vscode.ViewColumn.Beside,
    { enableScripts: false }
  );

  const files = (manifest.files || [])
    .map(
      (f) =>
        `<li><code>${escapeHtml(f.path)}</code> <span class="muted">${escapeHtml(
          f.digest || ""
        )}</span></li>`
    )
    .join("");

  const cap = manifest.capability || {};
  const replayLink = `mathevidence://replay?path=${encodeURIComponent(bundleDir)}`;

  panel.webview.html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<style>
  :root {
    --bg: #f4f6f8;
    --ink: #1a2332;
    --muted: #5a6a7a;
    --computed: #2b6cb0;
    --tested: #2f855a;
    --certified: #1a365d;
    --ambiguous: #9b2c2c;
    --panel: #ffffff;
    --rule: #d0d7de;
  }
  body {
    font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
    color: var(--ink);
    background:
      radial-gradient(1200px 600px at 10% -10%, #dce8f5 0%, transparent 55%),
      radial-gradient(900px 500px at 100% 0%, #e8eef4 0%, transparent 50%),
      var(--bg);
    margin: 0;
    padding: 1.25rem 1.5rem 2rem;
  }
  h1 { font-size: 1.35rem; margin: 0 0 0.35rem; letter-spacing: -0.02em; }
  .sub { color: var(--muted); margin-bottom: 1.25rem; }
  .state {
    display: inline-block;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-size: 0.8rem;
    border: 2px solid currentColor;
    padding: 0.35rem 0.65rem;
    margin-bottom: 0.75rem;
  }
  .Computed { color: var(--computed); }
  .Tested { color: var(--tested); }
  .Certified { color: var(--certified); }
  .Ambiguous { color: var(--ambiguous); }
  .card {
    background: var(--panel);
    border: 1px solid var(--rule);
    padding: 1rem 1.1rem;
    margin: 0.75rem 0;
  }
  .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
  code, pre { font-family: "IBM Plex Mono", Consolas, monospace; font-size: 0.85rem; }
  ul { padding-left: 1.1rem; }
  .muted { color: var(--muted); font-size: 0.8rem; }
  a { color: var(--computed); }
</style>
</head>
<body>
  <div class="state ${epistemic.label}">${epistemic.label}</div>
  <h1>${escapeHtml(cap.id || "unknown capability")}</h1>
  <p class="sub">${escapeHtml(epistemic.detail)}</p>

  <div class="card">
    <div class="label">Result status (machine)</div>
    <div><code>${escapeHtml(manifest.resultStatus || "")}</code>
      · claim <code>${escapeHtml(manifest.claimClass || "")}</code>
      · assurance <code>${escapeHtml(manifest.assuranceMode || "")}</code></div>
  </div>

  <div class="card">
    <div class="label">Request digest</div>
    <div><code>${escapeHtml(manifest.requestDigest || "")}</code></div>
  </div>

  <div class="card">
    <div class="label">Bundle files</div>
    <ul>${files}</ul>
  </div>

  <div class="card">
    <div class="label">Replay link</div>
    <p><code>${escapeHtml(replayLink)}</code></p>
    <p class="muted">Use command <strong>MathEvidence: Replay Evidence Bundle</strong> to run offline Python digest/schema checks. Lean kernel replay is separate.</p>
  </div>
</body>
</html>`;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

class EvidenceTreeProvider {
  constructor() {
    this._onDidChangeTreeData = new vscode.EventEmitter();
    this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    /** @type {string|undefined} */
    this.bundleDir = undefined;
    /** @type {object|undefined} */
    this.manifest = undefined;
    /** @type {{ label: EpistemicLabel, detail: string }|undefined} */
    this.epistemic = undefined;
  }

  refresh(bundleDir, manifest, epistemic) {
    this.bundleDir = bundleDir;
    this.manifest = manifest;
    this.epistemic = epistemic;
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element) {
    return element;
  }

  getChildren() {
    if (!this.manifest || !this.epistemic) {
      const item = new vscode.TreeItem(
        "Open an Evidence Bundle…",
        vscode.TreeItemCollapsibleState.None
      );
      item.command = {
        command: "mathevidence.openBundle",
        title: "Open Evidence Bundle",
      };
      return [item];
    }
    const state = new vscode.TreeItem(
      `State: ${this.epistemic.label}`,
      vscode.TreeItemCollapsibleState.None
    );
    state.description = this.manifest.resultStatus;
    state.tooltip = this.epistemic.detail;

    const cap = new vscode.TreeItem(
      `Capability: ${(this.manifest.capability || {}).id || "?"}`,
      vscode.TreeItemCollapsibleState.None
    );
    const digest = new vscode.TreeItem(
      "Request digest",
      vscode.TreeItemCollapsibleState.None
    );
    digest.description = this.manifest.requestDigest;

    const replay = new vscode.TreeItem(
      "Replay bundle",
      vscode.TreeItemCollapsibleState.None
    );
    replay.command = {
      command: "mathevidence.replayBundle",
      title: "Replay",
      arguments: [this.bundleDir],
    };

    return [state, cap, digest, replay];
  }
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  const tree = new EvidenceTreeProvider();
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("mathevidence.evidenceExplorer", tree)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("mathevidence.showEpistemicLegend", async () => {
      const lines = [
        "Computed — backend/candidate only",
        "Tested — offline schema/digest checks",
        "Certified — Lean-verified status (confirm kernel replay)",
        "Ambiguous — missing, rejected, unsupported, or unclear",
      ];
      await vscode.window.showInformationMessage(lines.join(" · "));
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("mathevidence.openBundle", async () => {
      const uris = await vscode.window.showOpenDialog({
        canSelectFiles: false,
        canSelectFolders: true,
        canSelectMany: false,
        openLabel: "Open Evidence Bundle",
      });
      if (!uris || !uris.length) {
        return;
      }
      const bundleDir = uris[0].fsPath;
      try {
        const manifest = loadManifest(bundleDir);
        const epistemic = epistemicFromResultStatus(
          manifest.resultStatus,
          manifest.leanStatus || manifest.leanReplayStatus
        );
        tree.refresh(bundleDir, manifest, epistemic);
        showBundlePanel(context, bundleDir, manifest, epistemic);
        await vscode.window.showInformationMessage(
          `MathEvidence: ${epistemic.label} — ${manifest.resultStatus || "unknown"}`
        );
      } catch (err) {
        await vscode.window.showErrorMessage(`MathEvidence: ${err.message || err}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "mathevidence.replayBundle",
      async (bundleDirArg) => {
        let bundleDir = bundleDirArg;
        if (!bundleDir) {
          const uris = await vscode.window.showOpenDialog({
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: "Replay Evidence Bundle",
          });
          if (!uris || !uris.length) {
            return;
          }
          bundleDir = uris[0].fsPath;
        }

        const cfg = vscode.workspace.getConfiguration("mathevidence");
        const python = cfg.get("pythonPath") || "python";
        const script = path.join(
          context.extensionPath,
          "..",
          "..",
          "scripts",
          "offline_replay_python.py"
        );
        const repoRoot = path.join(context.extensionPath, "..", "..");

        await vscode.window.withProgress(
          {
            location: vscode.ProgressLocation.Notification,
            title: "MathEvidence offline replay",
          },
          async () => {
            const result = await runPythonReplay(python, script, repoRoot, bundleDir);
            if (result.code === 0) {
              const epistemic = epistemicFromResultStatus("tested");
              try {
                const manifest = loadManifest(bundleDir);
                tree.refresh(bundleDir, manifest, epistemic);
              } catch (_) {
                /* ignore */
              }
              const link = `mathevidence://replay?path=${encodeURIComponent(bundleDir)}`;
              await vscode.window.showInformationMessage(
                `MathEvidence: Tested — offline replay ok. Link: ${link}`
              );
            } else {
              await vscode.window.showErrorMessage(
                `MathEvidence: Ambiguous/rejected — replay failed.\n${result.stderr || result.stdout}`
              );
            }
          }
        );
      }
    )
  );
}

function runPythonReplay(python, script, cwd, bundleDir) {
  return new Promise((resolve) => {
    // Prefer SDK local replay if dedicated single-bundle CLI is unavailable.
    const args = ["-m", "agent.sdk", "--local", "replay-bundle", bundleDir];
    const child = spawn(python, args, { cwd, shell: false });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => {
      stdout += d.toString();
    });
    child.stderr.on("data", (d) => {
      stderr += d.toString();
    });
    child.on("close", (code) => {
      // Parse JSON resultStatus when possible
      let ok = code === 0;
      try {
        const parsed = JSON.parse(stdout);
        ok = parsed.resultStatus === "tested";
      } catch (_) {
        /* keep exit code */
      }
      resolve({ code: ok ? 0 : code || 1, stdout, stderr });
    });
    child.on("error", (err) => {
      resolve({ code: 1, stdout, stderr: String(err) });
    });
  });
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
  epistemicFromResultStatus,
};
