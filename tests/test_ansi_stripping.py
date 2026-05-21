from pytk.filters.git import GitFilter
from pytk.filters.test import TestFilter
from pytk.filters.grep import GrepFilter


def test_git_status_strips_ansi():
    f = GitFilter()
    output = "\x1b[32mmodified:   src/foo.py\x1b[0m\n\x1b[31mdeleted:    src/bar.py\x1b[0m"
    result = f.filter(output, ["git", "status"])
    assert "\x1b[" not in result
    assert "modified" in result


def test_pytest_strips_ansi():
    f = TestFilter()
    output = "\x1b[32mPASSED\x1b[0m tests/test_foo.py::test_bar\n\x1b[31mFAILED\x1b[0m tests/test_baz.py::test_qux\n\x1b[1m===== 1 failed, 1 passed =====\x1b[0m"
    result = f.filter(output, ["pytest"])
    assert "\x1b[" not in result
    assert "FAILED" in result


def test_grep_strips_ansi():
    f = GrepFilter()
    output = "\x1b[35msrc/foo.py\x1b[0m:\x1b[32m10\x1b[0m:def my_function():\nsrc/bar.py:20:def other():"
    result = f.filter(output, ["grep", "-rn", "def"])
    assert "\x1b[" not in result


def test_strip_ansi_util():
    from pytk.filters.base import strip_ansi
    assert strip_ansi("\x1b[32mhello\x1b[0m world") == "hello world"
    assert strip_ansi("no escapes") == "no escapes"
    assert strip_ansi("") == ""
    assert strip_ansi("\x1b[1;31mBold Red\x1b[0m") == "Bold Red"
