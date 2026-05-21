import pytest
from pytk.filters.lint import LintFilter


def test_matches_ruff():
    f = LintFilter()
    assert f.matches(['ruff', 'check', '.'])
    assert f.matches(['mypy', 'src/'])
    assert f.matches(['flake8', 'src/'])
    assert f.matches(['pylint', 'src/'])
    assert f.matches(['tsc', '--noEmit'])
    assert not f.matches(['pytest'])
    assert not f.matches(['git'])


def test_ruff_clean():
    f = LintFilter()
    result = f.filter('All checks passed.\n', ['ruff', 'check'])
    assert result == 'ruff: no issues found'


def test_ruff_with_errors():
    f = LintFilter()
    output = 'src/foo.py:10:5: E501 Line too long (120 > 88 characters)\nsrc/bar.py:3:1: F401 `os` imported but unused\n'
    result = f.filter(output, ['ruff', 'check'])
    assert 'E501' in result
    assert 'F401' in result


def test_mypy_clean():
    f = LintFilter()
    result = f.filter('Success: no issues found in 12 source files\n', ['mypy'])
    assert 'no issues found' in result


def test_mypy_errors():
    f = LintFilter()
    output = 'src/foo.py:10: error: Incompatible return value type\nsrc/bar.py:3: warning: Unused type ignore\nFound 2 errors in 1 file\n'
    result = f.filter(output, ['mypy'])
    assert 'error' in result
    assert 'Found 2 errors' in result


def test_flake8_clean():
    f = LintFilter()
    result = f.filter('', ['flake8'])
    assert result == 'flake8: no issues found'


def test_tsc_clean():
    f = LintFilter()
    result = f.filter('', ['tsc', '--noEmit'])
    assert result == 'tsc: no errors'


def test_tsc_errors():
    f = LintFilter()
    output = 'src/index.ts(10,5): error TS2345: Argument type string not assignable\nsrc/util.ts(3,1): error TS2304: Cannot find name foo\n'
    result = f.filter(output, ['tsc', '--noEmit'])
    assert 'TS2345' in result
    assert 'TS2304' in result
    assert len(result.splitlines()) == 2


def test_ansi_stripped():
    f = LintFilter()
    output = '\x1b[31msrc/foo.py:1:1: E501 too long\x1b[0m\n'
    result = f.filter(output, ['ruff'])
    assert '\x1b[' not in result
    assert 'E501' in result
