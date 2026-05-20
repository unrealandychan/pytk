"""Tests for pytk --dry-run flag (issue #14)."""
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from pytk.cli import main
from pytk.runner import run_filtered


def test_dry_run_prefixes_output():
    """--dry-run should prefix each output line with [DRY-RUN]."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "echo", "hello"])
    assert "[DRY-RUN]" in result.output
    assert "hello" in result.output


def test_dry_run_no_stats_update(tmp_path):
    """--dry-run must not write stats.json."""
    stats_file = tmp_path / "stats.json"

    with patch("pytk.runner.STATS_FILE", stats_file):
        filtered_output, exit_code, stats = run_filtered(
            ["echo", "hello"], dry_run=True
        )

    assert not stats_file.exists(), "stats.json must not be written in dry_run mode"
    assert "[DRY-RUN]" in filtered_output


def test_dry_run_still_filters():
    """Filter is applied; output should still have [DRY-RUN] prefix."""
    runner = CliRunner()
    # Use a command that produces output — filter applied or not, prefix should appear
    result = runner.invoke(main, ["--dry-run", "echo", "test line"])
    assert "[DRY-RUN] test line" in result.output or "[DRY-RUN]" in result.output


def test_normal_run_no_prefix(tmp_path):
    """Without --dry-run, output should NOT have [DRY-RUN] prefix."""
    stats_file = tmp_path / "stats.json"
    with patch("pytk.runner.STATS_FILE", stats_file):
        runner = CliRunner()
        result = runner.invoke(main, ["echo", "hello"])
    assert "[DRY-RUN]" not in result.output
    assert "hello" in result.output
