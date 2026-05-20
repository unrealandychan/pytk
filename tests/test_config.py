import pytest
import tomllib
from pathlib import Path
from pytk.config import load_config, _deep_merge, _find_project_config, get_filter_config, DEFAULTS


def test_defaults_returned_when_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = load_config(tmp_path)
    assert cfg["filters"]["cat"]["max_lines"] == 200


def test_deep_merge():
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    override = {"a": {"y": 99, "z": 4}, "c": 5}
    result = _deep_merge(base, override)
    assert result == {"a": {"x": 1, "y": 99, "z": 4}, "b": 3, "c": 5}


def test_project_config_overrides_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".pytk.toml").write_text('[filters.cat]\nmax_lines = 500\n')
    cfg = load_config(tmp_path)
    assert cfg["filters"]["cat"]["max_lines"] == 500
    # other defaults still present
    assert cfg["filters"]["grep"]["max_results"] == 50


def test_user_config_overrides_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    pytk_dir = tmp_path / ".pytk"
    pytk_dir.mkdir()
    (pytk_dir / "config.toml").write_text('[filters.grep]\nmax_results = 100\n')
    cfg = load_config(tmp_path)
    assert cfg["filters"]["grep"]["max_results"] == 100


def test_project_overrides_user(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    pytk_dir = tmp_path / ".pytk"
    pytk_dir.mkdir()
    (pytk_dir / "config.toml").write_text('[filters.cat]\nmax_lines = 300\n')
    (tmp_path / ".pytk.toml").write_text('[filters.cat]\nmax_lines = 999\n')
    cfg = load_config(tmp_path)
    assert cfg["filters"]["cat"]["max_lines"] == 999


def test_find_project_config_walks_parents(tmp_path, monkeypatch):
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (tmp_path / ".pytk.toml").write_text("[global]\nenabled = true\n")
    found = _find_project_config(deep)
    assert found == tmp_path / ".pytk.toml"


def test_get_filter_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = load_config(tmp_path)
    cat_cfg = get_filter_config(cfg, "cat")
    assert cat_cfg["max_lines"] == 200


def test_unknown_key_returns_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = load_config(tmp_path)
    assert get_filter_config(cfg, "nonexistent") == {}


# CLI tests
from click.testing import CliRunner
from pytk.cli import main as cli


def test_config_show(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert "filters" in data


def test_config_get(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "get", "filters.cat.max_lines"])
    assert result.exit_code == 0
    assert "200" in result.output


def test_config_set_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "set", "filters.cat.max_lines", "500"])
    assert result.exit_code == 0
    cfg_path = tmp_path / ".pytk.toml"
    assert cfg_path.exists()
    with open(cfg_path, "rb") as f:
        data = tomllib.load(f)
    assert data["filters"]["cat"]["max_lines"] == 500
