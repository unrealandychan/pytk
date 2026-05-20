from pytk.filters.git import GitFilter

f = GitFilter()

GIT_STATUS_OUTPUT = """\
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   src/pytk/cli.py
	modified:   src/pytk/runner.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	tests/new_test.py

hint: Use 'git push' to publish your local commits.
no changes added to commit (use "git add" and/or "git commit -a")
"""

GIT_DIFF_OUTPUT = """\
diff --git a/src/pytk/cli.py b/src/pytk/cli.py
index abc1234..def5678 100644
--- a/src/pytk/cli.py
+++ b/src/pytk/cli.py
@@ -1,5 +1,6 @@
 import click
+import sys
 from rich.console import Console
"""

GIT_PUSH_OUTPUT = """\
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 8 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 512 bytes | 512.00 KiB/s, done.
Total 3 (delta 2), reused 0 (delta 0)
To github.com:user/repo.git
   abc1234..def5678  main -> origin/main
Branch 'main' set up to track remote branch 'main' from 'origin'.
"""

GIT_COMMIT_OUTPUT = """\
[main abc1234] Add new filter
 3 files changed, 45 insertions(+), 2 deletions(-)
 create mode 100644 src/pytk/filters/cat.py
"""

GIT_LOG_OUTPUT = """\
commit abc123456789
Author: Alice <alice@example.com>
Date:   Mon May 20 07:00:00 2026 +0000

    Add cat filter

commit def987654321
Author: Bob <bob@example.com>
Date:   Sun May 19 20:00:00 2026 +0000

    Initial commit
"""


def test_git_matches():
    assert f.matches(["git", "status"])
    assert f.matches(["git", "diff", "HEAD~1"])
    assert not f.matches(["ls", "-la"])


def test_git_status_strips_hints():
    result = f.filter(GIT_STATUS_OUTPUT, ["git", "status"])
    assert "hint:" not in result
    # Inline (use "git add"...) instructions should be stripped
    lines = result.splitlines()
    assert not any(l.strip().startswith('(use') and 'git' in l for l in lines)
    assert "cli.py" in result


def test_git_status_keeps_changed_files():
    result = f.filter(GIT_STATUS_OUTPUT, ["git", "status"])
    assert "cli.py" in result
    assert "runner.py" in result


def test_git_diff_strips_index_lines():
    result = f.filter(GIT_DIFF_OUTPUT, ["git", "diff"])
    assert "index abc1234..def5678" not in result
    assert "@@ -1,5 +1,6 @@" in result
    assert "+import sys" in result


def test_git_push_compressed():
    result = f.filter(GIT_PUSH_OUTPUT, ["git", "push"])
    assert "→" in result or "->" in result
    # Should be a single line summary
    lines = [l for l in result.splitlines() if l.strip()]
    assert len(lines) == 1


def test_git_commit_compressed():
    result = f.filter(GIT_COMMIT_OUTPUT, ["git", "commit"])
    assert "committed:" in result
    assert "abc1234" in result


def test_git_log_strips_author_date():
    result = f.filter(GIT_LOG_OUTPUT, ["git", "log"])
    assert "Author:" not in result
    assert "Date:" not in result
    assert "Add cat filter" in result
    assert "Initial commit" in result


def test_git_savings_example():
    ex = f.savings_example()
    assert ex["before"] > ex["after"]
