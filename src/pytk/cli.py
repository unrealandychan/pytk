import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from pytk.runner import run, run_filtered
from pytk.filters.registry import FILTERS

console = Console()
STATS_FILE = Path.home() / ".pytk" / "stats.json"


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
def gain():
    """Show token savings stats from ~/.pytk/stats.json."""
    if not STATS_FILE.exists():
        console.print("[yellow]No stats yet. Run some commands with pytk first.[/yellow]")
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

    if not records:
        console.print("[yellow]No stats yet.[/yellow]")
        return

    from collections import defaultdict
    by_cmd: dict[str, dict] = defaultdict(lambda: {"orig": 0, "filt": 0, "count": 0})
    total_orig = 0
    total_filt = 0

    for r in records:
        cmd = r.get("cmd", "unknown")
        by_cmd[cmd]["orig"] += r.get("orig_chars", 0)
        by_cmd[cmd]["filt"] += r.get("filt_chars", 0)
        by_cmd[cmd]["count"] += 1
        total_orig += r.get("orig_chars", 0)
        total_filt += r.get("filt_chars", 0)

    table = Table(title="pytk Token Savings", show_header=True, header_style="bold cyan")
    table.add_column("Command", style="bold")
    table.add_column("Runs", justify="right")
    table.add_column("Orig tokens", justify="right")
    table.add_column("Filt tokens", justify="right")
    table.add_column("Saved", justify="right", style="green")
    table.add_column("Reduction", justify="right", style="green")

    for cmd, data in sorted(by_cmd.items()):
        orig_tok = data["orig"] // 4
        filt_tok = data["filt"] // 4
        saved = orig_tok - filt_tok
        pct = (saved / orig_tok * 100) if orig_tok > 0 else 0
        table.add_row(cmd, str(data["count"]), str(orig_tok), str(filt_tok), str(saved), f"{pct:.0f}%")

    orig_tok_total = total_orig // 4
    filt_tok_total = total_filt // 4
    saved_total = orig_tok_total - filt_tok_total
    pct_total = (saved_total / orig_tok_total * 100) if orig_tok_total > 0 else 0
    table.add_row(
        "[bold]TOTAL[/bold]",
        str(len(records)),
        str(orig_tok_total),
        str(filt_tok_total),
        str(saved_total),
        f"{pct_total:.0f}%",
        style="bold",
    )

    console.print(table)


@main.command(name="init")
@click.option("--agent", default=None, help="Agent name: claude, hermes, codex")
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
