"""Tests for Claude Code PreToolUse hook."""
import json
import os
import sys
import io
import pytest
from unittest.mock import patch

from pytk.hooks.claude_hook import should_rewrite, rewrite_command, main


# ---- unit tests for should_rewrite ----

def test_should_rewrite_git():
    assert should_rewrite("git status") is True

def test_should_rewrite_pytest():
    assert should_rewrite("pytest tests/") is True

def test_should_rewrite_ls():
    assert should_rewrite("ls -la src/") is True

def test_should_rewrite_python_m_pytest():
    assert should_rewrite("python -m pytest tests/") is True

def test_should_rewrite_python3_m_pytest():
    assert should_rewrite("python3 -m pytest -v") is True

def test_no_rewrite_already_prefixed():
    assert should_rewrite("pytk git status") is False

def test_no_rewrite_pytk_alone():
    assert should_rewrite("pytk") is False

def test_no_rewrite_unknown_cmd():
    assert should_rewrite("make install") is False

def test_no_rewrite_empty():
    assert should_rewrite("") is False

def test_no_rewrite_echo():
    assert should_rewrite("echo hello") is False


# ---- unit tests for rewrite_command ----

def test_rewrite_command():
    assert rewrite_command("git status") == "pytk git status"

def test_rewrite_command_strips_whitespace():
    assert rewrite_command("  ls -la  ") == "pytk ls -la"


# ---- integration tests for main() ----

def _run_main(stdin_data: str):
    """Run main() with given stdin, return (stdout, exit_code)."""
    captured = io.StringIO()
    exit_code = None
    with patch("sys.stdin", io.StringIO(stdin_data)):
        with patch("sys.stdout", captured):
            try:
                main()
            except SystemExit as e:
                exit_code = e.code
    return captured.getvalue(), exit_code


def test_main_rewrites_bash_tool():
    inp = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}})
    out, code = _run_main(inp)
    assert code == 0
    data = json.loads(out.strip())
    assert data["updatedInput"]["command"] == "pytk git status"


def test_main_passthrough_already_prefixed():
    inp = json.dumps({"tool_name": "Bash", "tool_input": {"command": "pytk git status"}})
    out, code = _run_main(inp)
    assert code == 0
    assert out.strip() == ""


def test_main_passthrough_non_bash():
    inp = json.dumps({"tool_name": "Edit", "tool_input": {}})
    out, code = _run_main(inp)
    assert code == 0
    assert out.strip() == ""


def test_main_invalid_json():
    out, code = _run_main("not valid json{{")
    assert code == 0


def test_main_preserves_description():
    inp = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "grep foo src/ -r", "description": "Search code"}
    })
    out, code = _run_main(inp)
    assert code == 0
    data = json.loads(out.strip())
    assert data["updatedInput"]["command"] == "pytk grep foo src/ -r"
    assert data["updatedInput"]["description"] == "Search code"


# ---- CLI tests for pytk init --agent claude-hook ----

from click.testing import CliRunner
from pytk.cli import main as cli_main


def test_cli_init_claude_hook_creates_files(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli_main, ["init", "--agent", "claude-hook"])
        assert result.exit_code == 0
        assert os.path.exists(".claude/hooks/pytk_hook.py")
        assert os.path.exists(".claude/settings.json")
        with open(".claude/settings.json") as f:
            settings = json.load(f)
        pre_tool_use = settings["hooks"]["PreToolUse"]
        assert any(e.get("matcher") == "Bash" for e in pre_tool_use)


def test_cli_init_claude_hook_merges_settings(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Pre-create settings.json with some other content
        os.makedirs(".claude", exist_ok=True)
        existing = {"someOtherKey": "value", "hooks": {"PostToolUse": []}}
        with open(".claude/settings.json", "w") as f:
            json.dump(existing, f)
        result = runner.invoke(cli_main, ["init", "--agent", "claude-hook"])
        assert result.exit_code == 0
        with open(".claude/settings.json") as f:
            settings = json.load(f)
        # Other content preserved
        assert settings["someOtherKey"] == "value"
        assert "PostToolUse" in settings["hooks"]
        # New hook added
        pre_tool_use = settings["hooks"]["PreToolUse"]
        assert any(e.get("matcher") == "Bash" for e in pre_tool_use)


def test_cli_init_claude_hook_no_duplicate(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Run twice
        runner.invoke(cli_main, ["init", "--agent", "claude-hook"])
        runner.invoke(cli_main, ["init", "--agent", "claude-hook"])
        with open(".claude/settings.json") as f:
            settings = json.load(f)
        pre_tool_use = settings["hooks"]["PreToolUse"]
        bash_entries = [e for e in pre_tool_use if e.get("matcher") == "Bash"]
        assert len(bash_entries) == 1
        pytk_hooks = bash_entries[0]["hooks"]
        pytk_cmds = [h["command"] for h in pytk_hooks]
        assert pytk_cmds.count("python3 .claude/hooks/pytk_hook.py") == 1


def test_cli_hook_run_claude(tmp_path):
    """Test pytk hook run-claude rewrites commands."""
    runner = CliRunner()
    inp = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git log"}})
    result = runner.invoke(cli_main, ["hook", "run-claude"], input=inp)
    assert result.exit_code == 0
    data = json.loads(result.output.strip())
    assert data["updatedInput"]["command"] == "pytk git log"
