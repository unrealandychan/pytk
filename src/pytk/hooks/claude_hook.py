#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for pytk.
Transparently rewrites supported commands to use pytk prefix.

Usage: Add to .claude/settings.json PreToolUse hooks.
"""
import json
import sys


SUPPORTED_PREFIXES = {
    "git", "ls", "find", "tree",
    "pytest",
    "grep", "rg", "ag",
    "cat", "head", "tail",
    "docker", "docker-compose",
    "kubectl", "k",
    "npm", "yarn", "pnpm", "npx",
    "cargo", "rustc",
    "curl", "http", "wget",
}


def should_rewrite(command: str) -> bool:
    """Check if command should be prefixed with pytk."""
    cmd = command.strip()
    if cmd.startswith("pytk ") or cmd == "pytk":
        return False
    first_word = cmd.split()[0] if cmd.split() else ""
    if first_word in SUPPORTED_PREFIXES:
        return True
    if cmd.startswith("python -m pytest") or cmd.startswith("python3 -m pytest"):
        return True
    return False


def rewrite_command(command: str) -> str:
    """Prefix command with pytk."""
    return f"pytk {command.strip()}"


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command or not should_rewrite(command):
        sys.exit(0)

    new_command = rewrite_command(command)
    updated = dict(tool_input)
    updated["command"] = new_command

    print(json.dumps({"updatedInput": updated}))
    sys.exit(0)


if __name__ == "__main__":
    main()
