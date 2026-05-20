"""Tests for pytk.cache module (issue #16)."""
import time
import pytest

import pytk.cache as cache
from pytk import cache as cache_mod


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


def test_is_cacheable_git():
    assert cache.is_cacheable("git status") is True


def test_is_cacheable_ls():
    assert cache.is_cacheable("ls -la") is True


def test_not_cacheable_docker():
    assert cache.is_cacheable("docker ps") is False


def test_not_cacheable_npm():
    assert cache.is_cacheable("npm install") is False


def test_cache_get_miss():
    assert cache.get("git status", "/some/cwd") is None


def test_cache_set_and_get():
    cache.set("git status", "/some/cwd", "output here")
    result = cache.get("git status", "/some/cwd")
    assert result == "output here"


def test_cache_ttl_expiry():
    cache.set("ls", "/tmp", "file list")
    # Use ttl=0 so it's immediately expired
    result = cache.get("ls", "/tmp", ttl=0)
    assert result is None


def test_cache_different_cwd():
    cache.set("git status", "/repo/a", "output_a")
    cache.set("git status", "/repo/b", "output_b")
    assert cache.get("git status", "/repo/a") == "output_a"
    assert cache.get("git status", "/repo/b") == "output_b"


def test_cache_clear():
    cache.set("ls", "/tmp", "stuff")
    cache.set("git status", "/tmp", "other")
    assert cache.size() == 2
    cache.clear()
    assert cache.size() == 0


def test_no_cache_flag_bypasses(monkeypatch, tmp_path):
    """With no_cache=True, cache should not be populated or used."""
    from unittest.mock import patch, MagicMock
    from pytk.runner import run_filtered

    # Pre-populate cache with a known value
    cache.set("ls -la", str(tmp_path), "cached output")

    # Even with cache populated, no_cache=True should bypass and run the real command
    # We mock `run` to avoid actual subprocess
    with patch("pytk.runner.run", return_value=("fresh output\n", 0)) as mock_run:
        with patch("pytk.runner.get_filter", return_value=None):
            with patch("pytk.runner._append_stats"):
                output, exit_code, stats = run_filtered(
                    ["ls", "-la"], no_cache=True
                )
    assert output == "fresh output\n"
    mock_run.assert_called_once()
    # Cache should NOT be updated when no_cache=True
    # The old cached value should still be there unchanged
    assert cache.get("ls -la", str(tmp_path)) == "cached output"
