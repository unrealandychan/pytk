"""
3-layer config merge:
  1. hardcoded defaults
  2. ~/.pytk/config.toml  (user-level)
  3. .pytk.toml in cwd or any parent dir (project-level)
"""
import tomllib
from pathlib import Path
from typing import Any

DEFAULTS = {
    "global": {
        "enabled": True,
        "passthrough_on_error": True,
    },
    "filters": {
        "cat": {"max_lines": 200},
        "grep": {"max_results": 50},
        "ls": {"max_entries": 200},
        "git": {"diff_context_lines": 3, "log_max": 20},
        "pytest": {"show_warnings": False},
        "docker": {"logs_tail": 100},
        "npm": {"max_lines": 100},
        "cargo": {"max_warnings": 20},
    }
}

def _find_project_config(start: Path | None = None) -> Path | None:
    """Walk up from start dir looking for .pytk.toml"""
    d = start or Path.cwd()
    for parent in [d, *d.parents]:
        candidate = parent / ".pytk.toml"
        if candidate.exists():
            return candidate
    return None

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base (override wins)"""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result

def load_config(cwd: Path | None = None) -> dict:
    config = _deep_merge({}, DEFAULTS)

    # user config
    user_cfg = Path.home() / ".pytk" / "config.toml"
    if user_cfg.exists():
        with open(user_cfg, "rb") as f:
            user_data = tomllib.load(f)
        config = _deep_merge(config, user_data)

    # project config
    project_cfg = _find_project_config(cwd)
    if project_cfg:
        with open(project_cfg, "rb") as f:
            project_data = tomllib.load(f)
        config = _deep_merge(config, project_data)

    return config

def get_filter_config(config: dict, filter_name: str) -> dict:
    """Get config for a specific filter, falling back to empty dict"""
    return config.get("filters", {}).get(filter_name, {})
