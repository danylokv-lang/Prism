# Prism GUI

Electron desktop shell for Prism. Calls the real `prism` CLI (must be
installed and on PATH — see the repo root README) via IPC; no logic is
duplicated here.

## Run (dev)

```bash
npm install
npm start
```

## Build a downloadable .dmg

```bash
npm install
npm run dist
```

Produces `release/Prism-<version>-arm64.dmg` — double-click, drag `Prism.app`
to `Applications`, same install pattern as Claude/Cursor. The app still needs
the `prism` CLI installed separately (it's a separate Python tool, not
bundled) — if it's missing, the app shows a banner with the install command
instead of failing silently. `build/icon.icns` is the app icon (rendered from
`build/icon.html` via an offscreen Electron capture, then `sips`/`iconutil`).

## How it's wired

- Click the project card (bottom-left) to choose a project folder.
- **Project Scan**: `Run Scan` shells out to `prism scan <folder> --json`.
- **Env**: `Run Audit` shells out to `prism env <folder> --json`.
- **Explain**: type a path relative to the chosen folder and press Enter —
  shells out to `prism explain <path> --json`.
- **Recipes** / **Sessions**: still static placeholders — no CLI commands
  exist for these yet.

`src/prism-runner.js` resolves the `prism` binary (PATH first, falling back
to common pipx/homebrew locations) and runs it via `execFile` (no shell,
so paths are never injection-prone).
