from pytk.filters.test import TestFilter

f = TestFilter()

PYTEST_WITH_FAILURES = """\
============================= test session starts ==============================
platform linux -- Python 3.11.0, pytest-8.0.0, pluggy-1.0.0
collected 5 items

tests/test_foo.py::test_pass1 PASSED
tests/test_foo.py::test_pass2 PASSED
tests/test_foo.py::test_pass3 PASSED
tests/test_bar.py::test_fail1 FAILED
tests/test_bar.py::test_fail2 FAILED

=================================== FAILURES ===================================
_________________________________ test_fail1 _________________________________

    def test_fail1():
>       assert 1 == 2
E       AssertionError: assert 1 == 2

tests/test_bar.py:10: AssertionError
_________________________________ test_fail2 _________________________________

    def test_fail2():
>       assert "a" == "b"
E       AssertionError: assert 'a' == 'b'

tests/test_bar.py:14: AssertionError
=========================== short test summary info ============================
FAILED tests/test_bar.py::test_fail1 - AssertionError: assert 1 == 2
FAILED tests/test_bar.py::test_fail2 - AssertionError
3 passed, 2 failed in 0.42s
"""

PYTEST_ALL_PASSING = """\
============================= test session starts ==============================
collected 10 items

tests/test_foo.py::test_one PASSED
tests/test_foo.py::test_two PASSED
tests/test_foo.py::test_three PASSED
tests/test_foo.py::test_four PASSED
tests/test_foo.py::test_five PASSED
tests/test_foo.py::test_six PASSED
tests/test_foo.py::test_seven PASSED
tests/test_foo.py::test_eight PASSED
tests/test_foo.py::test_nine PASSED
tests/test_foo.py::test_ten PASSED

============================== 10 passed in 1.23s ==============================
"""


def test_pytest_matches():
    assert f.matches(["pytest", "tests/"])
    assert f.matches(["python", "-m", "pytest"])
    assert f.matches(["go", "test", "./..."])
    assert f.matches(["cargo", "test"])
    assert f.matches(["npm", "test"])
    assert not f.matches(["ls", "-la"])


def test_pytest_keeps_failures():
    result = f.filter(PYTEST_WITH_FAILURES, ["pytest", "tests/"])
    assert "AssertionError" in result
    assert "test_fail1" in result or "test_fail2" in result


def test_pytest_strips_passing():
    result = f.filter(PYTEST_WITH_FAILURES, ["pytest", "tests/"])
    # PASSED lines should be stripped
    assert "PASSED" not in result


def test_pytest_keeps_summary():
    result = f.filter(PYTEST_WITH_FAILURES, ["pytest", "tests/"])
    assert "passed" in result or "failed" in result


def test_pytest_all_passing_just_summary():
    result = f.filter(PYTEST_ALL_PASSING, ["pytest", "tests/"])
    # Should not have individual PASSED lines
    assert "PASSED" not in result
    assert "passed" in result


def test_pytest_savings_example():
    ex = f.savings_example()
    assert ex["before"] > ex["after"]
