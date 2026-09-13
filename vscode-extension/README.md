# ASEP VS Code Extension

**Lightweight VS Code Extension integrating the ASEP AI Engineering Playground control plane directly into your editor sidebar.**

---

## Features

- **Embedded Playground Sidebar**: Access your Next.js AI Playground directly inside VS Code without switching windows.
- **Local Port Bridge**: Automatically detects the active workspace folder and syncs its absolute path to the local Antigravity engine (`http://localhost:8000`).
- **File Explorer Sync**: Click generated code or file references in the Playground to open them directly in the VS Code editor at the specified line.
- **Direct Code Insertion**: Generated agent solutions can be inserted straight into your active text editor.
- **Quick Status Bar Toggle**: Launch or focus the Playground sidebar from the bottom status bar (`$(hubot) ASEP AI`).

---

## Configuration Settings

Under `Settings -> Extensions -> ASEP AI Engineering`:

| Setting | Default | Description |
|---|---|---|
| `asep.dashboardUrl` | `http://localhost:3000` | URL of the frontend dashboard (supports localhost or production `https://asep-ai.vercel.app`). |
| `asep.backendUrl` | `http://127.0.0.1:8000` | Base URL of the FastAPI backend engine. |
| `asep.bridgePort` | `8000` | Port for local Antigravity engine IPC. |
| `asep.autoSyncWorkspace` | `true` | Automatically sends workspace folder paths on folder change. |

---

## Development & Packaging

1. Install dependencies:
   ```bash
   cd vscode-extension
   npm install
   ```
2. Compile TypeScript:
   ```bash
   npm run compile
   ```
3. Press `F5` in VS Code to launch an Extension Development Host window.
4. To package as `.vsix`:
   ```bash
   npx @vscode/vsce package
   ```