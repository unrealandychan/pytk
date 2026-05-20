# pytk — Token Killer for VS Code

[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/unrealandychan.pytk-vscode)](https://marketplace.visualstudio.com/items?itemName=unrealandychan.pytk-vscode)

Reduce LLM token usage by filtering verbose shell output directly in your VS Code terminal. Works seamlessly with AI coding assistants like Claude, Codex, and Cursor.

## What it does

`pytk` (Token Killer) hooks into your shell and strips boilerplate, noise, and redundant output from commands like `pip install`, `npm install`, `git`, `docker`, and more — before that output reaches your AI assistant's context window.

This extension:
- Shows **cumulative token savings** in the VS Code status bar (e.g. `⚡ pytk: 73% saved`)
- Provides commands to enable/disable filtering on the fly
- Opens a **savings report** panel showing per-command token reduction stats
- Prompts you to run `pytk hook enable` when a new terminal session starts

## Requirements

**pytk must be installed on your system.**

```bash
# Install with uv (recommended)
uv tool install pytk

# Or with pip
pip install pytk
```

Verify it works:
```bash
pytk --version
```

## Installation

### From the VS Code Marketplace
1. Open VS Code
2. Go to **Extensions** (`Ctrl+Shift+X` / `Cmd+Shift+X`)
3. Search for **pytk Token Killer**
4. Click **Install**

### From a `.vsix` file
1. Download the latest `.vsix` from [GitHub Releases](https://github.com/unrealandychan/pytk/releases)
2. In VS Code: **Extensions → ⋯ → Install from VSIX…**
3. Select the downloaded file

## Usage

### Status bar
Once active, the status bar (bottom right) shows:
- `⚡ pytk: 73% saved` — percentage of characters filtered across all recorded commands
- `⚡ pytk: active` — pytk is enabled but no stats yet
- `⚡ pytk: off` — filtering is disabled

Click the status bar item to open the full savings report.

### Commands

Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run:

| Command | Description |
|---------|-------------|
| `pytk: Enable filtering` | Turn on terminal output filtering |
| `pytk: Disable filtering` | Turn off terminal output filtering |
| `pytk: Show token savings` | Open the savings report webview |

### Shell hook

For automatic filtering of every command you run, enable the shell hook:

```bash
pytk hook enable
```

This adds a shell function that wraps your commands and pipes output through `pytk filter`. The VS Code extension will prompt you to do this automatically when it detects a new terminal session with shell integration active.

To remove the hook:
```bash
pytk hook disable
```

## How it works

1. `pytk hook enable` adds a shell pre-exec hook to your `~/.bashrc` / `~/.zshrc`
2. Each command's output is piped through `pytk filter`, which removes noise
3. Stats are written to `~/.pytk/stats.json` (newline-delimited JSON)
4. This extension reads that file and displays aggregate savings in the status bar
5. Clicking the status bar item runs `pytk gain` and shows the formatted report

## Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `pytk.enabled` | boolean | `true` | Enable pytk terminal output filtering |
| `pytk.showStatusBar` | boolean | `true` | Show token savings in the status bar |
| `pytk.pytk_path` | string | `"pytk"` | Path to the pytk executable (use full path if not on `$PATH`) |

### Example: custom pytk path

If pytk is installed in a virtualenv or non-standard location:

```json
{
  "pytk.pytk_path": "/home/you/.local/bin/pytk"
}
```

## Stats file format

`~/.pytk/stats.json` is newline-delimited JSON. Each line is a record:

```json
{"command": "pip install", "orig_chars": 4821, "filt_chars": 312, "ts": "2024-01-15T10:23:44"}
```

The extension aggregates all records to compute the overall savings percentage.

## Troubleshooting

**Status bar shows `pytk: active` but no savings percentage**
→ No commands have been run through pytk yet. Run a command like `pip install requests` in the terminal after enabling the hook.

**`pytk: Show token savings` shows an error**
→ pytk is not found at the configured path. Check `pytk.pytk_path` in settings and ensure pytk is installed.

**Hook suggestion keeps appearing**
→ You can dismiss it or run `pytk hook enable` once to make it permanent.

## License

MIT
