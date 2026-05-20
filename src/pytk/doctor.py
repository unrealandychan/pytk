"""pytk doctor — environment health check."""
import json
import shutil
from pathlib import Path

import click

from pytk import __version__
from pytk.hook import hook_status

CHECK = "\u2714"
CROSS = "\u2718"
WARN = "\u26a0"


def _ok(msg):
    click.echo(click.style(f"{CHECK} {msg}", fg="green"))


def _fail(msg):
    click.echo(click.style(f"{CROSS} {msg}", fg="red"))


def _warn(msg):
    click.echo(click.style(f"{WARN} {msg}", fg="yellow"))


def run_doctor(cwd=None):
    """Run all doctor checks. Returns exit code (0 = ok, 1 = critical failure)."""
    import os
    cwd = Path(cwd) if cwd else Path(os.getcwd())
    exit_code = 0

    # 1. pytk version — always pass
    _ok(f"pytk {__version__} installed")

    # 2. Stats file
    stats_file = Path.home() / ".pytk" / "stats.json"
    if stats_file.exists():
        count = sum(1 for line in stats_file.read_text().splitlines() if line.strip())
        _ok(f"Stats file: {stats_file} ({count} entries)")
    else:
        _fail(f"Stats file: {stats_file} not found")

    # 3. Shell hook
    status = hook_status()
    if status["enabled"]:
        _ok(f"Shell hook: enabled ({status['config_file']})")
    else:
        _fail(f"Shell hook: not enabled (checked {status['config_file']})")

    # 4. Claude Code hook
    claude_hook = cwd / ".claude" / "hooks" / "pytk_hook.py"
    if claude_hook.exists():
        _ok(f"Claude Code hook: {claude_hook.relative_to(cwd)} found")
    else:
        _fail(f"Claude Code hook: .claude/hooks/pytk_hook.py not found")

    # 5. Gemini hook
    gemini_hook = cwd / ".gemini" / "hooks" / "pytk_hook.py"
    if gemini_hook.exists():
        _ok(f"Gemini hook: {gemini_hook.relative_to(cwd)} found")
    else:
        _fail(f"Gemini hook: .gemini/hooks/pytk_hook.py not found")

    # 6. Config file
    local_config = cwd / ".pytk.toml"
    global_config = Path.home() / ".pytk" / "config.toml"
    if local_config.exists():
        _ok(f"Config file: .pytk.toml")
    elif global_config.exists():
        _ok(f"Config file: {global_config}")
    else:
        _fail("Config file: no .pytk.toml or ~/.pytk/config.toml found")

    # 7. Filters loaded
    try:
        from pytk.filters.registry import FILTERS
        _ok(f"Filters loaded: {len(FILTERS)}")
        # Probe each filter with its class-name-derived command
        for f in FILTERS:
            name = type(f).__name__.replace("Filter", "").lower()
            # Try some common spellings
            candidates = [name]
            # Special cases
            specials = {
                "packagemanager": ["pip", "brew"],
                "test": ["pytest"],
                "cat": ["cat"],
                "grep": ["grep"],
                "curl": ["curl"],
                "kubectl": ["kubectl"],
                "make": ["make"],
                "terraform": ["terraform"],
                "npm": ["npm"],
                "cargo": ["cargo"],
                "docker": ["docker"],
                "git": ["git"],
                "ls": ["ls"],
            }
            cmds = specials.get(name, candidates)
            for cmd in cmds:
                path = shutil.which(cmd)
                if path:
                    _ok(f"  {cmd}: found at {path}")
                else:
                    _warn(f"  {cmd}: not in PATH")
    except Exception as e:
        _fail(f"Filters: failed to load ({e})")
        exit_code = 1

    return exit_code
