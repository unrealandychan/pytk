import subprocess
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pytk.filters.registry import get_filter
from pytk import cache as _cache_mod

STATS_FILE = Path.home() / ".pytk" / "stats.json"


def run(cmd: list[str], capture_env: bool = True) -> tuple[str, int]:
    """Execute cmd as subprocess, return (output, exit_code)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        output = result.stdout
        if result.stderr:
            output = output + result.stderr if output else result.stderr
        return output, result.returncode
    except FileNotFoundError:
        return f"pytk: command not found: {cmd[0]}\n", 127


def run_filtered(cmd: list[str], no_cache: bool = False, dry_run: bool = False) -> tuple[str, int, dict]:
    """Run cmd, apply filter, return (filtered_output, exit_code, stats)."""
    command_str = " ".join(cmd)
    cwd = os.getcwd()
    ttl = _cache_mod.DEFAULT_TTL

    if not no_cache and _cache_mod.is_cacheable(command_str):
        cached = _cache_mod.get(command_str, cwd, ttl)
        if cached is not None:
            stats = {"original_chars": len(cached), "filtered_chars": len(cached), "filter_name": "cache"}
            return cached, 0, stats

    output, exit_code = run(cmd)
    filt = get_filter(cmd)

    original_chars = len(output)
    filter_name = "none"

    if filt is not None:
        filtered_output = filt.filter(output, cmd)
        filter_name = type(filt).__name__
    else:
        filtered_output = output

    filtered_chars = len(filtered_output)

    stats = {
        "original_chars": original_chars,
        "filtered_chars": filtered_chars,
        "filter_name": filter_name,
    }

    if dry_run:
        prefixed_lines = "\n".join(
            f"[DRY-RUN] {line}" for line in filtered_output.splitlines()
        )
        if filtered_output.endswith("\n"):
            prefixed_lines += "\n"
        return prefixed_lines, exit_code, stats

    _append_stats(cmd, stats)

    if not no_cache and _cache_mod.is_cacheable(command_str):
        _cache_mod.set(command_str, cwd, filtered_output)

    return filtered_output, exit_code, stats


def _append_stats(cmd: list[str], stats: dict) -> None:
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "cmd": cmd[0] if cmd else "",
        "subcmd": cmd[1] if len(cmd) > 1 else "",
        "orig_chars": stats["original_chars"],
        "filt_chars": stats["filtered_chars"],
        "filter": stats["filter_name"],
    }
    with open(STATS_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
