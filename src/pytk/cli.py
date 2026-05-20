import csv
import io
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from pytk.runner import run, run_filtered
from pytk.filters.registry import FILTERS

console = Console()
STATS_FILE = Path.home() / ".pytk" / "stats.json"


def _parse_since(since_str: str):
    """Parse a since string like '7d', '30d', '1d' or 'YYYY-MM-DD' to a datetime cutoff."""
    if since_str is None:
        return None
    since_str = since_str.strip()
    if since_str.endswith("d") and since_str[:-1].isdigit():
        days = int(since_str[:-1])
        return datetime.now(timezone.utc) - timedelta(days=days)
    # Try YYYY-MM-DD
    try:
        dt = datetime.strptime(since_str, "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise click.BadParameter(f"Invalid --since value: {since_str!r}. Use '7d', '30d', or 'YYYY-MM-DD'.")


def _filter_stats_by_since(records, cutoff):
    """Filter stat records to those at or after cutoff."""
    if cutoff is None:
        return records
    filtered = []
    for r in records:
        ts_str = r.get("ts") or r.get("timestamp")
        if ts_str is None:
            continue
        try:
            ts_str_clean = ts_str.replace("Z", "+00:00")
            ts = datetime.fromisoformat(ts_str_clean)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                filtered.append(r)
        except ValueError:
            pass
    return filtered


def _compute_rows_totals(records):
    """Compute by-command rows and totals from records."""
    by_cmd = defaultdict(lambda: {"orig": 0, "filt": 0, "count": 0})
    total_orig = 0
    total_filt = 0

    for r in records:
        cmd = r.get("cmd") or r.get("command") or "unknown"
        orig = r.get("orig_chars") or r.get("original_tokens", 0) * 4
        filt = r.get("filt_chars") or r.get("filtered_tokens", 0) * 4
        by_cmd[cmd]["orig"] += orig
        by_cmd[cmd]["filt"] += filt
        by_cmd[cmd]["count"] += 1
        total_orig += orig
        total_filt += filt

    rows = []
    for cmd, data in sorted(by_cmd.items()):
        orig_tok = data["orig"] // 4
        filt_tok = data["filt"] // 4
        pct = ((orig_tok - filt_tok) / orig_tok * 100) if orig_tok > 0 else 0
        rows.append({"command": cmd, "runs": data["count"], "original": orig_tok, "filtered": filt_tok, "reduction_pct": round(pct, 1)})

    orig_tok_total = total_orig // 4
    filt_tok_total = total_filt // 4
    pct_total = ((orig_tok_total - filt_tok_total) / orig_tok_total * 100) if orig_tok_total > 0 else 0
    totals = {
        "runs": len(records),
        "original_tokens": orig_tok_total,
        "filtered_tokens": filt_tok_total,
        "reduction_pct": round(pct_total, 1),
    }
    return rows, totals


def _format_json(rows, totals, period="all-time"):
    data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "period": period,
        "totals": totals,
        "by_command": rows,
    }
    return json.dumps(data, indent=2)


def _format_csv(rows, totals):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Command", "Runs", "Original", "Filtered", "Reduction %"])
    for r in rows:
        writer.writerow([r["command"], r["runs"], r["original"], r["filtered"], r["reduction_pct"]])
    writer.writerow(["TOTAL", totals["runs"], totals["original_tokens"], totals["filtered_tokens"], totals["reduction_pct"]])
    return output.getvalue()


def _format_markdown(rows, totals):
    lines = [
        "| Command | Runs | Original | Filtered | Savings |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['command']} | {r['runs']} | {r['original']:,} | {r['filtered']:,} | {r['reduction_pct']:.0f}% |")
    lines.append(
        f"| **TOTAL** | **{totals['runs']}** | **{totals['original_tokens']:,}** | **{totals['filtered_tokens']:,}** | **{totals['reduction_pct']:.0f}%** |"
    )
    return "\n".join(lines) + "\n"


class PytkGroup(click.Group):
    """Click Group that falls through to run_filtered for unknown subcommands."""

    def parse_args(self, ctx, args):
        # Store all args in protected_args; we'll dispatch manually in invoke
        ctx.protected_args = list(args)
        ctx.args = []
        return []

    def invoke(self, ctx):
        args = list(ctx.protected_args) + list(ctx.args)
        ctx.protected_args = []
        ctx.args = []

        if not args:
            with ctx:
                return super(click.Group, self).invoke(ctx)

        cmd_name = args[0]
        cmd = self.get_command(ctx, cmd_name)

        if cmd is not None:
            with ctx:
                ctx.invoked_subcommand = cmd_name
                super(click.Group, self).invoke(ctx)
                sub_ctx = cmd.make_context(cmd_name, args[1:], parent=ctx)
                with sub_ctx:
                    return sub_ctx.command.invoke(sub_ctx)
        else:
            # Unknown command — proxy through run_filtered
            with ctx:
                super(click.Group, self).invoke(ctx)
            filtered_output, exit_code, stats = run_filtered(args)
            click.echo(filtered_output, nl=False)
            if filtered_output and not filtered_output.endswith("\n"):
                click.echo()
            sys.exit(exit_code)


@click.group(cls=PytkGroup, invoke_without_command=True)
@click.pass_context
def main(ctx):
    """pytk — CLI proxy that reduces LLM token consumption.

    \b
    Run any command with filtering:
      pytk ls -la src/
      pytk git status
      pytk pytest tests/

    \b
    Built-in commands:
      pytk gain            Show token savings
      pytk init            Print agent integration instructions
      pytk list-filters    Show registered filters
      pytk passthrough     Run command without filtering
    """


@main.command()
@click.option("--format", "-f", "fmt", type=click.Choice(["table", "json", "csv", "markdown"]), default="table", help="Output format")
@click.option("--since", default=None, help="Filter stats since '7d', '30d', '1d' or 'YYYY-MM-DD'")
@click.option("--reset", is_flag=True, default=False, help="Clear stats file after printing")
def gain(fmt, since, reset):
    """Show token savings stats from ~/.pytk/stats.json."""
    if not STATS_FILE.exists():
        if fmt == "table":
            console.print("[yellow]No stats yet. Run some commands with pytk first.[/yellow]")
        else:
            click.echo("No stats yet.")
        return

    records = []
    with open(STATS_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    cutoff = _parse_since(since)
    records = _filter_stats_by_since(records, cutoff)
    period = since if since else "all-time"

    if not records:
        if fmt == "table":
            console.print("[yellow]No stats yet.[/yellow]")
        else:
            click.echo("No stats yet.")
        if reset and STATS_FILE.exists():
            STATS_FILE.unlink()
        return

    rows, totals = _compute_rows_totals(records)

    if fmt == "json":
        click.echo(_format_json(rows, totals, period=period))
    elif fmt == "csv":
        click.echo(_format_csv(rows, totals), nl=False)
    elif fmt == "markdown":
        click.echo(_format_markdown(rows, totals), nl=False)
    else:
        table = Table(title="pytk Token Savings", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="bold")
        table.add_column("Runs", justify="right")
        table.add_column("Orig tokens", justify="right")
        table.add_column("Filt tokens", justify="right")
        table.add_column("Saved", justify="right", style="green")
        table.add_column("Reduction", justify="right", style="green")

        for r in rows:
            saved = r["original"] - r["filtered"]
            table.add_row(r["command"], str(r["runs"]), str(r["original"]), str(r["filtered"]), str(saved), f"{r['reduction_pct']:.0f}%")

        orig_tok_total = totals["original_tokens"]
        filt_tok_total = totals["filtered_tokens"]
        saved_total = orig_tok_total - filt_tok_total
        table.add_row(
            "[bold]TOTAL[/bold]",
            str(totals["runs"]),
            str(orig_tok_total),
            str(filt_tok_total),
            str(saved_total),
            f"{totals['reduction_pct']:.0f}%",
            style="bold",
        )
        console.print(table)

    if reset and STATS_FILE.exists():
        STATS_FILE.unlink()


PYTK_HOOK_PY_CONTENT = '''\
#!/usr/bin/env python3
"""pytk Claude Code PreToolUse hook. Auto-generated by pytk init."""
import json, sys

SUPPORTED = {
    "git", "ls", "find", "tree", "pytest",
    "grep", "rg", "ag", "cat", "head", "tail",
    "docker", "docker-compose", "kubectl", "k",
    "npm", "yarn", "pnpm", "npx",
    "cargo", "rustc", "curl", "http", "wget",
}

def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    tool_input = data.get("tool_input", {})
    cmd = tool_input.get("command", "").strip()
    first = cmd.split()[0] if cmd.split() else ""
    if not cmd or first not in SUPPORTED or cmd.startswith("pytk"):
        sys.exit(0)
    updated = dict(tool_input)
    updated["command"] = f"pytk {cmd}"
    print(json.dumps({"updatedInput": updated}))

if __name__ == "__main__":
    main()
'''


WINDSURF_PYTK_SECTION = """
# pytk Token Filter
# Always prefix the following commands with `pytk` to reduce token usage by 60-90%:
# git, ls, find, tree, pytest, grep, rg, cat, head, tail, docker, kubectl, npm, yarn, cargo, curl
#
# Example: instead of `git status`, use `pytk git status`
"""

PYTK_MARKER = "# pytk"


def _install_windsurf(agent_cwd=None):
    """Append pytk section to .windsurfrules (create if not exists)."""
    import os
    cwd = agent_cwd or os.getcwd()
    rules_path = os.path.join(cwd, ".windsurfrules")
    if os.path.exists(rules_path):
        with open(rules_path) as f:
            content = f.read()
    else:
        content = ""
    if PYTK_MARKER in content:
        click.echo(".windsurfrules already contains pytk section. Skipping.")
        return
    with open(rules_path, "a") as f:
        f.write(WINDSURF_PYTK_SECTION)
    click.echo(f"Updated {rules_path}")


GEMINI_HOOK_PY_CONTENT = '''\
#!/usr/bin/env python3
"""pytk Gemini CLI BeforeTool hook. Auto-generated by pytk init."""
import json, sys

SUPPORTED = {
    "git","ls","find","tree","pytest",
    "grep","rg","ag","cat","head","tail",
    "docker","docker-compose","kubectl","k",
    "npm","yarn","pnpm","npx",
    "cargo","rustc","curl","http","wget",
}

def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)
    tool_name = data.get("tool_name", data.get("toolName", ""))
    if tool_name not in ("Bash", "bash", "shell", "Shell"):
        sys.exit(0)
    tool_input = data.get("tool_input", data.get("toolInput", {}))
    cmd = tool_input.get("command", "").strip()
    first = cmd.split()[0] if cmd.split() else ""
    if not cmd or first not in SUPPORTED or cmd.startswith("pytk"):
        sys.exit(0)
    updated = dict(tool_input)
    updated["command"] = f"pytk {cmd}"
    print(json.dumps({"updatedInput": updated}))

if __name__ == "__main__":
    main()
'''


def _install_gemini_hook(agent_cwd=None):
    """Install Gemini CLI BeforeTool hook files in current directory."""
    import json as _json
    import os
    cwd = agent_cwd or os.getcwd()
    hooks_dir = os.path.join(cwd, ".gemini", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)

    hook_script = os.path.join(hooks_dir, "pytk_hook.py")
    with open(hook_script, "w") as f:
        f.write(GEMINI_HOOK_PY_CONTENT)
    os.chmod(hook_script, 0o755)
    click.echo(f"Created {hook_script}")

    settings_path = os.path.join(cwd, ".gemini", "settings.json")
    if os.path.exists(settings_path):
        with open(settings_path) as f:
            settings = _json.load(f)
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    before_tool = hooks.setdefault("BeforeTool", [])

    bash_entry = None
    for entry in before_tool:
        if entry.get("matcher") == "Bash":
            bash_entry = entry
            break

    pytk_hook_cmd = "python3 .gemini/hooks/pytk_hook.py"
    if bash_entry is None:
        before_tool.append({
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": pytk_hook_cmd}]
        })
    else:
        existing_cmds = [h.get("command") for h in bash_entry.get("hooks", [])]
        if pytk_hook_cmd not in existing_cmds:
            bash_entry.setdefault("hooks", []).append(
                {"type": "command", "command": pytk_hook_cmd}
            )
        else:
            click.echo("Hook already registered in .gemini/settings.json")

    with open(settings_path, "w") as f:
        _json.dump(settings, f, indent=2)
    click.echo(f"Updated {settings_path}")
    click.echo("\nGemini CLI BeforeTool hook installed!")


def _install_claude_hook():
    """Install Claude Code PreToolUse hook files in current directory."""
    import json as _json
    import os
    cwd = os.getcwd()
    hooks_dir = os.path.join(cwd, ".claude", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)

    hook_script = os.path.join(hooks_dir, "pytk_hook.py")
    with open(hook_script, "w") as f:
        f.write(PYTK_HOOK_PY_CONTENT)
    os.chmod(hook_script, 0o755)
    click.echo(f"Created {hook_script}")

    settings_path = os.path.join(cwd, ".claude", "settings.json")
    if os.path.exists(settings_path):
        with open(settings_path) as f:
            settings = _json.load(f)
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    # Check if Bash matcher already exists
    bash_entry = None
    for entry in pre_tool_use:
        if entry.get("matcher") == "Bash":
            bash_entry = entry
            break

    pytk_hook_cmd = "python3 .claude/hooks/pytk_hook.py"
    if bash_entry is None:
        pre_tool_use.append({
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": pytk_hook_cmd}]
        })
    else:
        existing_cmds = [h.get("command") for h in bash_entry.get("hooks", [])]
        if pytk_hook_cmd not in existing_cmds:
            bash_entry.setdefault("hooks", []).append(
                {"type": "command", "command": pytk_hook_cmd}
            )
        else:
            click.echo("Hook already registered in .claude/settings.json")

    with open(settings_path, "w") as f:
        _json.dump(settings, f, indent=2)
    click.echo(f"Updated {settings_path}")
    click.echo("\nClaude Code PreToolUse hook installed!")
    click.echo("Commands like `git`, `ls`, `pytest` will automatically use pytk.")


CURSOR_MDC_CONTENT = '''\
---
description: pytk token filter — compress shell output before it reaches context
alwaysApply: true
---

# pytk Token Filter

Always prefix the following commands with `pytk` to compress their output and reduce token usage:

- git (git status, git diff, git log, git show, etc.)
- ls, find, tree
- pytest, python -m pytest
- grep, rg, ag
- cat, head, tail
- docker, docker-compose
- kubectl
- npm, yarn, pnpm, npx
- cargo
- curl, http, wget

## Examples

```bash
# Instead of:
git status
# Use:
pytk git status

# Instead of:
pytest tests/
# Use:
pytk pytest tests/
```

This reduces token usage by 60–90% on verbose commands.
'''


def _install_cursor_rules(project_dir=None):
    """Install Cursor rules file in the project directory."""
    import os
    cwd = project_dir or os.getcwd()
    rules_dir = os.path.join(cwd, ".cursor", "rules")
    os.makedirs(rules_dir, exist_ok=True)

    mdc_path = os.path.join(rules_dir, "pytk.mdc")
    if os.path.exists(mdc_path):
        click.echo(f"{mdc_path} already exists — skipping.")
        return

    with open(mdc_path, "w") as f:
        f.write(CURSOR_MDC_CONTENT)
    click.echo(f"Created {mdc_path}")


@main.command(name="init")
@click.option("--agent", default=None, help="Agent name: claude, claude-hook, hermes, codex, cursor")
def init_cmd(agent):
    """Print integration instructions for AI coding agents."""
    agents = [agent] if agent else ["claude", "hermes", "codex"]
    for a in agents:
        if a == "claude":
            console.print("\n[bold cyan]## Claude Code (CLAUDE.md)[/bold cyan]\n")
            console.print(
                "Add to your CLAUDE.md:\n\n"
                "```markdown\n"
                "## Shell Commands\n"
                "Use `pytk <cmd>` instead of running shell commands directly.\n"
                "This reduces token usage by filtering verbose output.\n\n"
                "Examples:\n"
                "  pytk ls -la src/\n"
                "  pytk git status\n"
                "  pytk pytest tests/\n"
                "  pytk grep 'def run' src/ -r\n"
                "```\n"
            )
        elif a == "hermes":
            console.print("\n[bold cyan]## Hermes Agent Plugin[/bold cyan]\n")
            console.print(
                "Add to your Hermes agent config:\n\n"
                "```python\n"
                "# hermes_pytk_adapter.py\n"
                "import subprocess\n\n"
                "def shell(cmd: str) -> str:\n"
                "    \"\"\"Run shell command via pytk for token-efficient output.\"\"\"\n"
                "    result = subprocess.run(\n"
                "        ['pytk'] + cmd.split(),\n"
                "        capture_output=True, text=True\n"
                "    )\n"
                "    return result.stdout + result.stderr\n"
                "```\n"
            )
        elif a == "codex":
            console.print("\n[bold cyan]## Codex (AGENTS.md)[/bold cyan]\n")
            console.print(
                "Add to your AGENTS.md:\n\n"
                "```markdown\n"
                "## Shell Command Proxy\n"
                "Prefix shell commands with `pytk` to reduce output verbosity:\n\n"
                "  pytk ls, pytk git status, pytk pytest, pytk grep, pytk cat\n\n"
                "This saves tokens by stripping unnecessary output.\n"
                "```\n"
            )
        elif a == "claude-hook":
            _install_claude_hook()
        elif a == "cursor":
            _install_cursor_rules()
        elif a == "windsurf":
            _install_windsurf(agent_cwd=None)
        elif a == "gemini":
            _install_gemini_hook(agent_cwd=None)


@main.command()
@click.argument("command", nargs=-1, required=True)
def passthrough(command):
    """Run command without any filtering (escape hatch)."""
    cmd = list(command)
    output, exit_code = run(cmd)
    click.echo(output, nl=False)
    sys.exit(exit_code)


@main.group()
def config():
    """Manage pytk configuration."""
    pass


@config.command("show")
def config_show():
    """Show effective merged configuration."""
    import json
    from pytk.config import load_config
    cfg = load_config()
    console = Console()
    console.print_json(json.dumps(cfg, indent=2))


@config.command("get")
@click.argument("key")
def config_get(key: str):
    """Get a config value by dotted key (e.g. filters.cat.max_lines)."""
    from pytk.config import load_config
    cfg = load_config()
    parts = key.split(".")
    val = cfg
    for p in parts:
        if not isinstance(val, dict) or p not in val:
            click.echo(f"Key not found: {key}", err=True)
            raise SystemExit(1)
        val = val[p]
    click.echo(str(val))


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a config value in .pytk.toml (project config)."""
    import tomllib, tomli_w
    cfg_path = Path(".pytk.toml")
    if cfg_path.exists():
        with open(cfg_path, "rb") as f:
            existing = tomllib.load(f)
    else:
        existing = {}

    parts = key.split(".")
    d = existing
    for p in parts[:-1]:
        d = d.setdefault(p, {})
    last = parts[-1]
    try:
        if value.lower() in ("true", "false"):
            d[last] = value.lower() == "true"
        else:
            d[last] = int(value)
    except ValueError:
        try:
            d[last] = float(value)
        except ValueError:
            d[last] = value

    with open(cfg_path, "wb") as f:
        tomli_w.dump(existing, f)
    click.echo(f"Set {key} = {d[last]} in .pytk.toml")


@main.command(name="list-filters")
def list_filters():
    """Show all registered filters and example savings."""
    table = Table(title="pytk Registered Filters", show_header=True, header_style="bold cyan")
    table.add_column("Filter", style="bold")
    table.add_column("Before (tokens)", justify="right")
    table.add_column("After (tokens)", justify="right")
    table.add_column("Reduction", justify="right", style="green")
    table.add_column("Description")

    for f in FILTERS:
        ex = f.savings_example()
        before = ex.get("before", 0) // 4
        after = ex.get("after", 0) // 4
        pct = ((before - after) / before * 100) if before > 0 else 0
        table.add_row(
            type(f).__name__,
            str(before),
            str(after),
            f"{pct:.0f}%",
            ex.get("description", ""),
        )

    console.print(table)


@main.group()
def hook():
    """Manage shell hook for automatic command interception."""
    pass


@hook.command("enable")
@click.option("--shell", default=None, help="Shell type: bash, zsh, fish (auto-detected if omitted)")
def hook_enable(shell):
    """Enable pytk shell hook — auto-intercepts commands without pytk prefix."""
    from pytk.hook import enable_hook
    already, cfg = enable_hook(shell=shell)
    if already:
        click.echo(f"Hook already enabled in {cfg}")
    else:
        click.echo(f"Hook enabled in {cfg}")
        click.echo("Restart your shell or run: source " + cfg)


@hook.command("disable")
@click.option("--shell", default=None, help="Shell type: bash, zsh, fish")
def hook_disable(shell):
    """Disable pytk shell hook."""
    from pytk.hook import disable_hook
    was_enabled, cfg = disable_hook(shell=shell)
    if was_enabled:
        click.echo(f"Hook disabled from {cfg}")
        click.echo("Restart your shell or run: source " + cfg)
    else:
        click.echo(f"Hook not found in {cfg}")


@hook.command("status")
@click.option("--shell", default=None, help="Shell type: bash, zsh, fish")
def hook_status_cmd(shell):
    """Show whether pytk hook is active."""
    from pytk.hook import hook_status
    status = hook_status(shell=shell)
    state = "enabled" if status["enabled"] else "disabled"
    click.echo(f"Hook: {state}")
    click.echo(f"Shell: {status['shell']}")
    click.echo(f"Config: {status['config_file']}")


@hook.command("run-claude", hidden=True)
def hook_run_claude():
    """Used internally by Claude Code PreToolUse hook."""
    from pytk.hooks.claude_hook import main
    main()
