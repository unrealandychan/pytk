from pytk.filters.grep import GrepFilter

f = GrepFilter()

# 60 grep matches across different files
def make_grep_output(n: int) -> str:
    lines = []
    for i in range(n):
        lines.append(f"src/file{i % 5}.py:{i + 1}:    def run_{i}(self):")
    return "\n".join(lines)


SAME_FILE_GREP = "\n".join([
    f"src/runner.py:{i}:    def method_{i}()" for i in range(1, 9)
])

BINARY_GREP = """\
src/foo.py:1:def foo():
Binary file src/binary.bin matches
src/bar.py:2:def bar():
"""


def test_grep_matches():
    assert f.matches(["grep", "-r", "pattern"])
    assert f.matches(["rg", "pattern"])
    assert f.matches(["ag", "pattern"])
    assert not f.matches(["find", "."])


def test_grep_max_matches():
    output = make_grep_output(60)
    result = f.filter(output, ["grep", "-r", "def run"])
    result_lines = result.splitlines()
    # Should have truncation note
    assert any("more" in l for l in result_lines)


def test_grep_same_file_grouping():
    result = f.filter(SAME_FILE_GREP, ["grep", "-r", "method"])
    assert "[+5 more in src/runner.py]" in result
    # Should show first 3
    assert "method_1" in result or "method_0" in result


def test_grep_strips_binary():
    result = f.filter(BINARY_GREP, ["grep", "-r", "pattern"])
    assert "Binary file" not in result
    assert "foo" in result
    assert "bar" in result


def test_grep_savings_example():
    ex = f.savings_example()
    assert ex["before"] > ex["after"]
