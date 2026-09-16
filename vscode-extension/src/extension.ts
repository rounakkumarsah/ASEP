import * as vscode from 'vscode';
import * as http from 'http';
import * as https from 'https';
import * as url from 'url';

/**
 * ASEP — Autonomous Software Engineering Platform
 * VS Code Sidebar Webview Provider & Local Port Bridge Extension
 */

export function activate(context: vscode.ExtensionContext) {
  console.log('[ASEP Extension] Activating ASEP Playground extension...');

  // 1. Instantiate and register the Webview View Provider in the Activity Bar sidebar
  const provider = new AsepPlaygroundViewProvider(context.extensionUri, context);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      AsepPlaygroundViewProvider.viewType,
      provider,
      {
        webviewOptions: {
          retainContextWhenHidden: true, // Keep session active when sidebar tab switches
        },
      }
    )
  );

  // 2. Register commands for user interaction
  context.subscriptions.push(
    vscode.commands.registerCommand('asep.openPlayground', () => {
      vscode.commands.executeCommand('workbench.view.extension.asep-sidebar-view');
    }),

    vscode.commands.registerCommand('asep.syncWorkspace', async () => {
      await provider.syncCurrentWorkspace();
    }),

    vscode.commands.registerCommand('asep.refreshDashboard', () => {
      provider.refresh();
    })
  );

  // 3. Status Bar Item for quick one-click toggle
  const statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100
  );
  statusBarItem.command = 'asep.openPlayground';
  statusBarItem.text = '$(hubot) ASEP AI';
  statusBarItem.tooltip = 'Open ASEP AI Engineering Playground';
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  // 4. Auto-sync workspace directory when workspace folders change
  context.subscriptions.push(
    vscode.workspace.onDidChangeWorkspaceFolders(async () => {
      const config = vscode.workspace.getConfiguration('asep');
      if (config.get<boolean>('autoSyncWorkspace', true)) {
        await provider.syncCurrentWorkspace();
      }
    })
  );

  console.log('[ASEP Extension] Activated successfully.');
}

export function deactivate() {
  console.log('[ASEP Extension] Deactivated.');
}

/**
 * Webview View Provider embedding the Next.js Playground inside an iframe.
 */
class AsepPlaygroundViewProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'asep.playgroundView';
  private _view?: vscode.WebviewView;

  constructor(
    private readonly _extensionUri: vscode.Uri,
    private readonly _context: vscode.ExtensionContext
  ) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ): void {
    this._view = webviewView;

    // Enable scripts and restrict local resource access
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };

    // Render the initial webview HTML containing the embedded iframe
    this.updateWebviewHtml();

    // Listen for messages dispatched from inside the embedded dashboard iframe
    webviewView.webview.onDidReceiveMessage(async (message) => {
      switch (message.command) {
        case 'openFile':
          await this.handleOpenFile(message.filePath, message.line);
          break;

        case 'insertCode':
          await this.handleInsertCode(message.code);
          break;

        case 'getWorkspaceInfo':
          this.postWorkspaceInfo();
          break;

        case 'notify':
          if (message.type === 'error') {
            vscode.window.showErrorMessage(`[ASEP] ${message.text}`);
          } else if (message.type === 'warning') {
            vscode.window.showWarningMessage(`[ASEP] ${message.text}`);
          } else {
            vscode.window.showInformationMessage(`[ASEP] ${message.text}`);
          }
          break;

        case 'executeTerminal':
          this.handleExecuteTerminal(message.commandLine);
          break;
      }
    });

    // Update whenever configuration settings change
    this._context.subscriptions.push(
      vscode.workspace.onDidChangeConfiguration((e) => {
        if (e.affectsConfiguration('asep')) {
          this.updateWebviewHtml();
        }
      })
    );
  }

  public refresh(): void {
    if (this._view) {
      this.updateWebviewHtml();
    }
  }

  /**
   * Reads the currently opened workspace absolute path.
   */
  public getWorkspacePath(): string | null {
    const folders = vscode.workspace.workspaceFolders;
    if (folders && folders.length > 0) {
      return folders[0].uri.fsPath;
    }
    return null;
  }

  /**
   * Syncs the absolute workspace path to the ASEP backend engine's file-explorer API.
   */
  public async syncCurrentWorkspace(): Promise<void> {
    const workspacePath = this.getWorkspacePath();
    if (!workspacePath) {
      vscode.window.showWarningMessage('[ASEP] No active workspace directory open in VS Code.');
      return;
    }

    const config = vscode.workspace.getConfiguration('asep');
    const backendPort = config.get<number>('bridgePort', 8000);
    const backendHost = config.get<string>('backendHost', '127.0.0.1');
    const backendUrl = config.get<string>('backendUrl', `http://${backendHost}:${backendPort}`);

    const syncEndpoint = `${backendUrl}/api/v1/workspace/sync`;

    const payload = JSON.stringify({
      workspace_path: workspacePath,
      workspace_name: vscode.workspace.name || 'default',
      timestamp: new Date().toISOString(),
    });

    try {
      await this.postJson(syncEndpoint, payload);
      vscode.window.showInformationMessage(`[ASEP] Workspace synced to engine: ${workspacePath}`);
    } catch (err: any) {
      console.warn('[ASEP Extension] Direct backend sync skipped (backend offline or endpoint optional):', err.message);
      // Fallback: Notify the embedded webview directly via postMessage
      if (this._view) {
        this._view.webview.postMessage({
          type: 'WORKSPACE_UPDATED',
          workspacePath,
        });
      }
    }
  }

  /**
   * Constructs the HTML for the Webview, hosting the Next.js dashboard iframe.
   */
  private updateWebviewHtml(): void {
    if (!this._view) return;

    const config = vscode.workspace.getConfiguration('asep');
    const defaultDashboard = 'http://localhost:3000';
    const rawDashboardUrl = config.get<string>('dashboardUrl', defaultDashboard);
    const bridgePort = config.get<number>('bridgePort', 8000);
    const workspacePath = this.getWorkspacePath();

    // Construct target URL with local port bridge & workspace query parameters
    let targetUrl = rawDashboardUrl.replace(/\/+$/, '');
    if (!targetUrl.includes('/playground')) {
      targetUrl += '/playground';
    }

    const params = new URLSearchParams();
    if (workspacePath) {
      params.set('workspacePath', workspacePath);
      params.set('workspaceName', vscode.workspace.name || 'VSCode Workspace');
    }
    params.set('bridgePort', String(bridgePort));
    params.set('ideSource', 'vscode');

    const fullIframeSrc = `${targetUrl}?${params.toString()}`;

    // Security: Derive CSP allow-origin rules from targetUrl
    let cspOrigin = 'http://localhost:3000 http://127.0.0.1:3000 https://asep-ai.vercel.app';
    try {
      const parsed = new URL(rawDashboardUrl);
      cspOrigin += ` ${parsed.origin}`;
    } catch {
      // Fallback to default origins
    }

    this._view.webview.html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="
    default-src 'none';
    frame-src ${cspOrigin} *;
    script-src 'unsafe-inline' 'unsafe-eval' vscode-resource:;
    style-src 'unsafe-inline';
    connect-src ${cspOrigin} http://127.0.0.1:* http://localhost:* https:;
  ">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ASEP AI Engineering Playground</title>
  <style>
    html, body {
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background-color: #0D1117;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    #container {
      width: 100%;
      height: 100%;
      position: relative;
      display: flex;
      flex-direction: column;
    }
    #dashboard-frame {
      width: 100%;
      height: 100%;
      border: none;
      flex: 1;
    }
    #loading-indicator {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      background-color: #0D1117;
      color: #94A3B8;
      font-size: 12px;
      z-index: 10;
      transition: opacity 0.3s ease;
    }
    .spinner {
      width: 28px;
      height: 28px;
      border: 3px solid rgba(34, 211, 238, 0.15);
      border-top-color: #22D3EE;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div id="container">
    <div id="loading-indicator">
      <div class="spinner"></div>
      <div>Connecting to ASEP Playground...</div>
    </div>
    <iframe
      id="dashboard-frame"
      src="${fullIframeSrc}"
      allow="clipboard-read; clipboard-write; microphone; camera;"
      sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
    ></iframe>
  </div>

  <script>
    const vscode = acquireVsCodeApi();
    const iframe = document.getElementById('dashboard-frame');
    const loading = document.getElementById('loading-indicator');

    iframe.onload = () => {
      loading.style.opacity = '0';
      setTimeout(() => {
        loading.style.display = 'none';
      }, 300);
    };

    // Forward postMessages from parent VS Code Webview to inside iframe
    window.addEventListener('message', (event) => {
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage(event.data, '*');
      }
    });

    // Listen to messages emitted by embedded dashboard and relay to extension.ts
    window.addEventListener('message', (event) => {
      if (event.data && event.data.source === 'asep-dashboard') {
        vscode.postMessage(event.data);
      }
    });
  </script>
</body>
</html>`;
  }

  /**
   * Opens a file in the active VS Code editor window.
   */
  private async handleOpenFile(filePath: string, line?: number): Promise<void> {
    try {
      const uri = vscode.Uri.file(filePath);
      const doc = await vscode.workspace.openTextDocument(uri);
      const editor = await vscode.window.showTextDocument(doc);
      if (line && line > 0) {
        const position = new vscode.Position(line - 1, 0);
        editor.selection = new vscode.Selection(position, position);
        editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);
      }
    } catch (err: any) {
      vscode.window.showErrorMessage(`[ASEP] Could not open file: ${filePath} (${err.message})`);
    }
  }

  /**
   * Inserts generated code directly at the cursor position in the active text editor.
   */
  private async handleInsertCode(code: string): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('[ASEP] Open an editor file to insert code.');
      return;
    }
    await editor.edit((editBuilder) => {
      editBuilder.insert(editor.selection.active, code);
    });
    vscode.window.showInformationMessage('[ASEP] Code inserted into active file.');
  }

  /**
   * Posts current workspace path and files back to the webview.
   */
  private postWorkspaceInfo(): void {
    if (!this._view) return;
    const workspacePath = this.getWorkspacePath();
    this._view.webview.postMessage({
      type: 'WORKSPACE_INFO',
      workspacePath,
      workspaceName: vscode.workspace.name || null,
    });
  }

  /**
   * Opens and executes commands inside a dedicated VS Code terminal.
   */
  private handleExecuteTerminal(commandLine: string): void {
    const terminal = vscode.window.activeTerminal || vscode.window.createTerminal('ASEP Terminal');
    terminal.show();
    terminal.sendText(commandLine);
  }

  /**
   * Helper utility to perform local HTTP POST without extra dependencies.
   */
  private postJson(targetUrl: string, body: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const parsed = url.parse(targetUrl);
      const isHttps = parsed.protocol === 'https:';
      const transport = isHttps ? https : http;

      const req = transport.request(
        {
          hostname: parsed.hostname,
          port: parsed.port || (isHttps ? 443 : 80),
          path: parsed.path,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(body),
          },
          timeout: 4000,
        },
        (res) => {
          let data = '';
          res.on('data', (chunk) => (data += chunk));
          res.on('end', () => resolve(data));
        }
      );

      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Request timed out'));
      });
      req.write(body);
      req.end();
    });
  }
}