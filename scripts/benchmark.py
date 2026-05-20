#!/usr/bin/env python3
"""
pytk benchmark — measure real token savings on actual commands.

Runs commands raw vs through pytk, counts tokens with tiktoken,
prints a markdown table suitable for the README.

Usage:
    python scripts/benchmark.py [--runs N] [--model cl100k_base]
"""
import argparse
import subprocess
import sys
from pathlib import Path

import tiktoken

PYTK = str(Path(__file__).parent.parent / ".venv" / "bin" / "pytk")
# Fallback: use the venv from close-wiki if local venv doesn't exist
if not Path(PYTK).exists():
    PYTK = "/home/ubuntu/close-wiki/.venv/bin/pytk"
if not Path(PYTK).exists():
    PYTK = "pytk"


def count_tokens(text: str, enc) -> int:
    return len(enc.encode(text))


def run_cmd(cmd: str, prefix: str, cwd: str) -> str:
    """Run a command (with optional prefix) and return combined stdout+stderr."""
    full = f"{prefix} {cmd}".strip() if prefix else cmd
    try:
        result = subprocess.run(
            full, shell=True, capture_output=True, text=True, cwd=cwd, timeout=30
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "(timeout)"
    except Exception as e:
        return str(e)


# Commands to benchmark — real AI coding session workloads
# (label, shell_command)
COMMANDS = [
    ("git status",           "git status"),
    ("git diff HEAD~1",      "git diff HEAD~1"),
    ("git log --oneline -20","git log --oneline -20"),
    ("ls -la",               "ls -la"),
    ("find *.py",            "find . -name '*.py' -not -path './.git/*'"),
    ("grep 'def '",          "grep -r 'def ' src/pytk/ --include='*.py' -n"),
    ("cat cli.py",           "cat src/pytk/cli.py"),
    ("pytest -v",            "python -m pytest tests/ -v 2>&1 || true"),
]


def benchmark(runs: int, model: str, cwd: str):
    enc = tiktoken.get_encoding(model)
    print(f"pytk benchmark")
    print(f"  cwd:      {cwd}")
    print(f"  encoding: {model}")
    print(f"  runs:     {runs} per command")
    print(f"  pytk:     {PYTK}\n")

    results = []
    for label, cmd in COMMANDS:
        raw_totals, filt_totals = [], []

        for _ in range(runs):
            raw_out   = run_cmd(cmd, "",    cwd)
            filt_out  = run_cmd(cmd, PYTK,  cwd)
            raw_totals.append(count_tokens(raw_out,  enc))
            filt_totals.append(count_tokens(filt_out, enc))

        avg_raw  = int(sum(raw_totals)  / runs)
        avg_filt = int(sum(filt_totals) / runs)
        saving   = int((1 - avg_filt / avg_raw) * 100) if avg_raw > 0 else 0

        results.append((label, avg_raw, avg_filt, saving))
        bar = "█" * (saving // 5) + "░" * (20 - saving // 5)
        print(f"  {label:28s}  raw={avg_raw:>6,}  filt={avg_filt:>6,}  -{saving:2d}%  [{bar}]")

    total_raw  = sum(r[1] for r in results)
    total_filt = sum(r[2] for r in results)
    total_pct  = int((1 - total_filt / total_raw) * 100) if total_raw > 0 else 0

    # ── Markdown table ──────────────────────────────────────────────────────
    print("\n\n" + "─" * 60)
    print("## Token Savings — Real Benchmark\n")
    print(f"> Measured on pytk's own codebase using `tiktoken` "
          f"({model} encoding), {runs} run(s) per command.\n")
    print("| Operation | Raw tokens | With pytk | Savings |")
    print("|---|---:|---:|:---:|")
    for label, raw, filt, pct in results:
        print(f"| `{label}` | {raw:,} | {filt:,} | **-{pct}%** |")
    print(f"| **Total** | **{total_raw:,}** | **{total_filt:,}** | **-{total_pct}%** |")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark pytk token savings")
    parser.add_argument("--runs",  type=int, default=3,
                        help="Runs per command (default: 3)")
    parser.add_argument("--model", default="cl100k_base",
                        help="tiktoken encoding (default: cl100k_base)")
    parser.add_argument("--cwd",   default=str(Path(__file__).parent.parent),
                        help="Working directory (default: repo root)")
    args = parser.parse_args()
    benchmark(args.runs, args.model, args.cwd)
