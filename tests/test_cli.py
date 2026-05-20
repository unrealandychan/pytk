from click.testing import CliRunner
from pytk.cli import main


def test_cli_passthrough():
    runner = CliRunner()
    result = runner.invoke(main, ["passthrough", "echo", "hello"])
    assert "hello" in result.output


def test_cli_list_filters():
    runner = CliRunner()
    result = runner.invoke(main, ["list-filters"])
    assert result.exit_code == 0
    assert "Filter" in result.output or "GitFilter" in result.output


def test_cli_init_claude():
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--agent", "claude"])
    assert result.exit_code == 0
    assert "CLAUDE.md" in result.output or "pytk" in result.output


def test_cli_init_hermes():
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--agent", "hermes"])
    assert result.exit_code == 0
    assert "hermes" in result.output.lower() or "plugin" in result.output.lower()


def test_cli_init_codex():
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--agent", "codex"])
    assert result.exit_code == 0
    assert "AGENTS.md" in result.output or "pytk" in result.output


def test_cli_gain_no_stats(tmp_path, monkeypatch):
    monkeypatch.setattr("pytk.cli.STATS_FILE", tmp_path / "nonexistent_stats.json")
    runner = CliRunner()
    result = runner.invoke(main, ["gain"])
    assert result.exit_code == 0
    assert "No stats" in result.output
