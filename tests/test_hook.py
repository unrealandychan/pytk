import pytest
from pathlib import Path
from pytk.hook import enable_hook, disable_hook, hook_status, _is_enabled, SENTINEL_START, SENTINEL_END
from click.testing import CliRunner
from pytk.cli import main as cli


def test_enable_writes_bash(tmp_path):
    cfg = tmp_path / ".bashrc"
    already, path = enable_hook(shell="bash", cfg_file=cfg)
    assert not already
    assert cfg.exists()
    content = cfg.read_text()
    assert SENTINEL_START in content
    assert SENTINEL_END in content
    assert "_pytk_proxy" in content
    assert "alias git" in content


def test_enable_writes_zsh(tmp_path):
    cfg = tmp_path / ".zshrc"
    already, path = enable_hook(shell="zsh", cfg_file=cfg)
    assert not already
    assert SENTINEL_START in cfg.read_text()


def test_enable_idempotent(tmp_path):
    cfg = tmp_path / ".bashrc"
    already1, _ = enable_hook(shell="bash", cfg_file=cfg)
    already2, _ = enable_hook(shell="bash", cfg_file=cfg)
    assert not already1
    assert already2  # second call reports already enabled
    # sentinel appears exactly once
    content = cfg.read_text()
    assert content.count(SENTINEL_START) == 1


def test_disable_removes_section(tmp_path):
    cfg = tmp_path / ".bashrc"
    enable_hook(shell="bash", cfg_file=cfg)
    was_enabled, _ = disable_hook(shell="bash", cfg_file=cfg)
    assert was_enabled
    content = cfg.read_text()
    assert SENTINEL_START not in content
    assert SENTINEL_END not in content


def test_disable_when_not_enabled(tmp_path):
    cfg = tmp_path / ".bashrc"
    cfg.write_text("# existing content\n")
    was_enabled, _ = disable_hook(shell="bash", cfg_file=cfg)
    assert not was_enabled
    # original content preserved
    assert "# existing content" in cfg.read_text()


def test_disable_preserves_surrounding_content(tmp_path):
    cfg = tmp_path / ".bashrc"
    cfg.write_text("# line before\n")
    enable_hook(shell="bash", cfg_file=cfg)
    with open(cfg, "a") as f:
        f.write("# line after\n")
    disable_hook(shell="bash", cfg_file=cfg)
    content = cfg.read_text()
    assert "# line before" in content
    assert "# line after" in content
    assert SENTINEL_START not in content


def test_status_active(tmp_path):
    cfg = tmp_path / ".bashrc"
    enable_hook(shell="bash", cfg_file=cfg)
    status = hook_status(shell="bash", cfg_file=cfg)
    assert status["enabled"] is True
    assert status["shell"] == "bash"


def test_status_inactive(tmp_path):
    cfg = tmp_path / ".bashrc"
    status = hook_status(shell="bash", cfg_file=cfg)
    assert status["enabled"] is False


def test_fish_hook_syntax(tmp_path):
    cfg = tmp_path / "config.fish"
    enable_hook(shell="fish", cfg_file=cfg)
    content = cfg.read_text()
    assert "function git" in content
    assert "pytk git $argv" in content


# CLI tests
def test_cli_hook_enable(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".bashrc").write_text("")
    runner = CliRunner()
    result = runner.invoke(cli, ["hook", "enable", "--shell", "bash"])
    assert result.exit_code == 0
    assert "enabled" in result.output


def test_cli_hook_disable(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = tmp_path / ".bashrc"
    enable_hook(shell="bash", cfg_file=cfg)
    runner = CliRunner()
    result = runner.invoke(cli, ["hook", "disable", "--shell", "bash"])
    assert result.exit_code == 0


def test_cli_hook_status(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["hook", "status", "--shell", "bash"])
    assert result.exit_code == 0
    assert "disabled" in result.output or "enabled" in result.output
