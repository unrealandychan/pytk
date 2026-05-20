"""Tests for pytk init --agent windsurf and --agent gemini."""
import json
import os
import pytest
from click.testing import CliRunner
from pytk.cli import main, _install_windsurf, _install_gemini_hook


# ── Windsurf ──────────────────────────────────────────────────────────────────

def test_init_windsurf_creates_file(tmp_path):
    _install_windsurf(agent_cwd=str(tmp_path))
    rules = tmp_path / ".windsurfrules"
    assert rules.exists()
    content = rules.read_text()
    assert "# pytk" in content
    assert "pytk git status" in content


def test_init_windsurf_appends_to_existing(tmp_path):
    rules = tmp_path / ".windsurfrules"
    rules.write_text("# existing content\n")
    _install_windsurf(agent_cwd=str(tmp_path))
    content = rules.read_text()
    assert "# existing content" in content
    assert "# pytk" in content


def test_init_windsurf_skips_if_already_present(tmp_path):
    rules = tmp_path / ".windsurfrules"
    rules.write_text("# pytk Token Filter\nalready here\n")
    _install_windsurf(agent_cwd=str(tmp_path))
    content = rules.read_text()
    # Should not have been appended again
    assert content.count("# pytk") == 1


# ── Gemini ────────────────────────────────────────────────────────────────────

def test_init_gemini_creates_hook_and_settings(tmp_path):
    _install_gemini_hook(agent_cwd=str(tmp_path))
    hook = tmp_path / ".gemini" / "hooks" / "pytk_hook.py"
    settings_path = tmp_path / ".gemini" / "settings.json"
    assert hook.exists()
    assert "BeforeTool" in hook.read_text() or "Gemini" in hook.read_text()
    assert settings_path.exists()
    settings = json.loads(settings_path.read_text())
    before_tool = settings["hooks"]["BeforeTool"]
    assert any(e.get("matcher") == "Bash" for e in before_tool)


def test_init_gemini_merges_existing_settings(tmp_path):
    gemini_dir = tmp_path / ".gemini"
    gemini_dir.mkdir()
    existing = {"someOtherKey": "value", "hooks": {"OtherHook": []}}
    (gemini_dir / "settings.json").write_text(json.dumps(existing))
    _install_gemini_hook(agent_cwd=str(tmp_path))
    settings = json.loads((gemini_dir / "settings.json").read_text())
    assert settings["someOtherKey"] == "value"
    assert "BeforeTool" in settings["hooks"]


def test_init_gemini_no_duplicate(tmp_path):
    _install_gemini_hook(agent_cwd=str(tmp_path))
    _install_gemini_hook(agent_cwd=str(tmp_path))
    settings = json.loads((tmp_path / ".gemini" / "settings.json").read_text())
    before_tool = settings["hooks"]["BeforeTool"]
    bash_entries = [e for e in before_tool if e.get("matcher") == "Bash"]
    assert len(bash_entries) == 1
    cmds = [h["command"] for h in bash_entries[0]["hooks"]]
    assert cmds.count("python3 .gemini/hooks/pytk_hook.py") == 1
