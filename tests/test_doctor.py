"""Tests for pytk doctor command."""
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from pytk import __version__
from pytk.cli import main
from pytk.filters.registry import FILTERS


def invoke_doctor(cwd=None):
    runner = CliRunner()
    if cwd:
        with runner.isolated_filesystem():
            os.chdir(cwd)
            result = runner.invoke(main, ["doctor"])
    else:
        result = runner.invoke(main, ["doctor"])
    return result


def test_doctor_runs_without_error():
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    # Exit 0 = all critical checks pass; non-zero is acceptable for non-critical
    # Per spec, critical checks are "pytk installed" and "filters registry loads" — both always pass
    assert result.exit_code == 0


def test_doctor_shows_version():
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert __version__ in result.output


def test_doctor_shows_filters():
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    # Should mention filter count
    assert "Filters loaded" in result.output
    # Should mention at least one filter-related command name
    assert any(
        name in result.output
        for name in ["git", "docker", "pytest", "terraform", "kubectl"]
    )


def test_doctor_claude_hook_found(tmp_path):
    hook_dir = tmp_path / ".claude" / "hooks"
    hook_dir.mkdir(parents=True)
    hook_file = hook_dir / "pytk_hook.py"
    hook_file.write_text("# fake hook")

    runner = CliRunner()
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(main, ["doctor"])
    finally:
        os.chdir(old_cwd)

    assert "\u2714" in result.output or "found" in result.output
    assert "Claude Code hook" in result.output
    # The checkmark should appear for claude hook line
    lines = result.output.splitlines()
    claude_line = next((l for l in lines if "Claude Code hook" in l), "")
    assert "\u2714" in claude_line


def test_doctor_claude_hook_missing(tmp_path):
    runner = CliRunner()
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(main, ["doctor"])
    finally:
        os.chdir(old_cwd)

    assert "Claude Code hook" in result.output
    lines = result.output.splitlines()
    claude_line = next((l for l in lines if "Claude Code hook" in l), "")
    assert "\u2718" in claude_line
