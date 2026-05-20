from pytk.filters.cat import CatFilter

f = CatFilter()


def make_lines(n: int) -> str:
    return "\n".join(f"Line {i}" for i in range(1, n + 1))


BLANK_LINES_INPUT = "line1\n\n\n\n\nline2\n\n\nline3"


def test_cat_matches():
    assert f.matches(["cat", "file.txt"])
    assert f.matches(["head", "-n", "50", "file.txt"])
    assert f.matches(["tail", "-f", "log.txt"])
    assert f.matches(["less", "file.txt"])
    assert not f.matches(["grep", "pattern"])


def test_cat_short_file_unchanged():
    short = make_lines(50)
    result = f.filter(short, ["cat", "file.txt"])
    assert "Line 1" in result
    assert "Line 50" in result
    assert "truncated" not in result


def test_cat_truncates_long_file():
    long_output = make_lines(300)
    result = f.filter(long_output, ["cat", "file.txt"])
    result_lines = result.splitlines()
    assert any("truncated" in l for l in result_lines)
    assert len(result_lines) <= 200 + 5  # head + note + tail


def test_cat_truncated_shows_head_and_tail():
    long_output = make_lines(300)
    result = f.filter(long_output, ["cat", "file.txt"])
    assert "Line 1" in result
    assert "Line 300" in result  # tail should include last line


def test_cat_strips_blank_lines():
    result = f.filter(BLANK_LINES_INPUT, ["cat", "file.txt"])
    lines = result.splitlines()
    # Count consecutive blanks
    max_consecutive = 0
    current = 0
    for line in lines:
        if line.strip() == "":
            current += 1
            max_consecutive = max(max_consecutive, current)
        else:
            current = 0
    assert max_consecutive <= 2


def test_cat_savings_example():
    ex = f.savings_example()
    assert ex["before"] > ex["after"]
