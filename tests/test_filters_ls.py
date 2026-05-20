from pytk.filters.ls import LsFilter

LS_LA_OUTPUT = """\
total 48
drwxr-xr-x  5 user group 4096 May 20 07:00 .
drwxr-xr-x 12 user group 4096 May 20 06:00 ..
-rw-r--r--  1 user group  512 May 20 07:00 README.md
-rw-r--r--  1 user group 1024 May 20 07:00 pyproject.toml
drwxr-xr-x  3 user group 4096 May 20 07:00 src
drwxr-xr-x  2 user group 4096 May 20 07:00 tests
-rw-r--r--  1 user group  256 May 20 07:00 .gitignore
"""

f = LsFilter()


def test_ls_matches():
    assert f.matches(["ls", "-la"])
    assert f.matches(["find", ".", "-name", "*.py"])
    assert f.matches(["tree"])
    assert not f.matches(["cat", "file.txt"])


def test_ls_filter_removes_permissions():
    result = f.filter(LS_LA_OUTPUT, ["ls", "-la"])
    assert "drwxr-xr-x" not in result
    assert "-rw-r--r--" not in result
    assert "README.md" in result
    assert "pyproject.toml" in result


def test_ls_filter_removes_total_line():
    result = f.filter(LS_LA_OUTPUT, ["ls", "-la"])
    assert "total 48" not in result


def test_ls_filter_truncates_long():
    # Generate 60 file entries
    lines = ["total 240"]
    for i in range(60):
        lines.append(f"-rw-r--r--  1 user group 100 May 20 07:00 file{i:03d}.txt")
    output = "\n".join(lines)
    result = f.filter(output, ["ls", "-la"])
    result_lines = result.splitlines()
    assert any("more entries" in l for l in result_lines)
    # Should be 50 + 1 truncation note = 51
    assert len(result_lines) <= 52


def test_ls_filter_find_passthrough():
    find_output = "./src/pytk/__init__.py\n./src/pytk/cli.py\n./tests/test_cli.py\n"
    result = f.filter(find_output, ["find", ".", "-name", "*.py"])
    assert "cli.py" in result


def test_ls_savings_example():
    ex = f.savings_example()
    assert ex["before"] > ex["after"]
    assert "description" in ex
