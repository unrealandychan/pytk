"""Tests for pytk gain command export features (issue #9)."""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from pytk.cli import main


SAMPLE_RECORDS = [
    {
        "ts": "2026-05-20T10:00:00Z",
        "cmd": "git",
        "orig_chars": 28800,
        "filt_chars": 2880,
        "filter": "GitFilter",
    },
    {
        "ts": "2026-05-20T10:01:00Z",
        "cmd": "ls",
        "orig_chars": 4000,
        "filt_chars": 1000,
        "filter": "LsFilter",
    },
    {
        "ts": "2026-05-19T09:00:00Z",
        "cmd": "git",
        "orig_chars": 8000,
        "filt_chars": 800,
        "filter": "GitFilter",
    },
]


def write_stats(path: Path, records=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if records is None:
        records = SAMPLE_RECORDS
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


@pytest.fixture()
def tmp_stats(tmp_path):
    stats_file = tmp_path / ".pytk" / "stats.json"
    write_stats(stats_file)
    with mock.patch("pytk.cli.STATS_FILE", stats_file):
        yield stats_file


def test_gain_default_table(tmp_stats):
    runner = CliRunner()
    result = runner.invoke(main, ["gain"])
    assert result.exit_code == 0
    # Rich table output should contain column headers
    assert "Command" in result.output or "Orig" in result.output or "Runs" in result.output


def test_gain_json_format(tmp_stats):
    runner = CliRunner()
    result = runner.invoke(main, ["gain", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "generated_at" in data
    assert "totals" in data
    assert "by_command" in data
    assert data["totals"]["runs"] == 3
    assert isinstance(data["by_command"], list)
    assert any(r["command"] == "git" for r in data["by_command"])


def test_gain_csv_format(tmp_stats):
    runner = CliRunner()
    result = runner.invoke(main, ["gain", "--format", "csv"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    # First line is header
    assert lines[0].startswith("Command")
    # Last line is TOTAL
    assert lines[-1].startswith("TOTAL")


def test_gain_markdown_format(tmp_stats):
    runner = CliRunner()
    result = runner.invoke(main, ["gain", "--format", "markdown"])
    assert result.exit_code == 0
    assert "|" in result.output
    assert "TOTAL" in result.output
    assert "Command" in result.output


def test_gain_since_days(tmp_path):
    stats_file = tmp_path / ".pytk" / "stats.json"
    now = datetime.now(timezone.utc)
    old_ts = (now - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent_ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    records = [
        {"ts": old_ts, "cmd": "git", "orig_chars": 4000, "filt_chars": 400, "filter": "GitFilter"},
        {"ts": recent_ts, "cmd": "ls", "orig_chars": 2000, "filt_chars": 200, "filter": "LsFilter"},
    ]
    write_stats(stats_file, records)
    with mock.patch("pytk.cli.STATS_FILE", stats_file):
        runner = CliRunner()
        result = runner.invoke(main, ["gain", "--format", "json", "--since", "1d"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        # Only the recent record should be counted
        assert data["totals"]["runs"] == 1
        assert data["by_command"][0]["command"] == "ls"


def test_gain_reset(tmp_stats):
    runner = CliRunner()
    result = runner.invoke(main, ["gain", "--reset"])
    assert result.exit_code == 0
    assert not tmp_stats.exists(), "Stats file should be deleted after --reset"


def test_gain_no_stats(tmp_path):
    missing_stats = tmp_path / ".pytk" / "stats.json"
    with mock.patch("pytk.cli.STATS_FILE", missing_stats):
        runner = CliRunner()
        result = runner.invoke(main, ["gain"])
        assert result.exit_code == 0
        # Should not crash, should print a message
        assert "No stats" in result.output


def test_gain_no_stats_json_format(tmp_path):
    missing_stats = tmp_path / ".pytk" / "stats.json"
    with mock.patch("pytk.cli.STATS_FILE", missing_stats):
        runner = CliRunner()
        result = runner.invoke(main, ["gain", "--format", "json"])
        assert result.exit_code == 0
        assert "No stats" in result.output
