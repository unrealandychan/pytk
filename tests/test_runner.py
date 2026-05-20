from pytk.filters.registry import get_filter
from pytk.filters.git import GitFilter
from pytk.filters.test import TestFilter
from pytk.filters.ls import LsFilter
from pytk.filters.grep import GrepFilter
from pytk.filters.cat import CatFilter


def test_registry_routes_git():
    filt = get_filter(["git", "status"])
    assert isinstance(filt, GitFilter)


def test_registry_routes_pytest():
    filt = get_filter(["pytest", "tests/"])
    assert isinstance(filt, TestFilter)


def test_registry_routes_ls():
    filt = get_filter(["ls", "-la"])
    assert isinstance(filt, LsFilter)


def test_registry_routes_grep():
    filt = get_filter(["grep", "-r", "pattern", "."])
    assert isinstance(filt, GrepFilter)


def test_registry_routes_cat():
    filt = get_filter(["cat", "README.md"])
    assert isinstance(filt, CatFilter)


def test_registry_no_match():
    filt = get_filter(["docker", "build", "."])
    assert filt is None


def test_registry_empty_cmd():
    filt = get_filter([])
    assert filt is None
