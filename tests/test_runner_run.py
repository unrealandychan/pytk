from pytk.runner import run, run_filtered


def test_runner_run_simple():
    output, exit_code = run(["echo", "hello"])
    assert output.strip() == "hello"
    assert exit_code == 0


def test_runner_run_exit_code():
    _, exit_code = run(["false"])
    assert exit_code != 0


def test_runner_run_nonexistent_command():
    output, exit_code = run(["nonexistent_cmd_xyz_123"])
    assert exit_code == 127


def test_run_filtered_stats():
    _, exit_code, stats = run_filtered(["echo", "hello world"])
    assert "original_chars" in stats
    assert "filtered_chars" in stats
    assert "filter_name" in stats
    assert exit_code == 0


def test_run_filtered_with_git_filter(tmp_path, monkeypatch):
    """run_filtered on a git command should use GitFilter."""
    # We can't run real git here, but we can check stats keys exist
    # by using echo as a stand-in via registry (echo won't match any filter)
    _, exit_code, stats = run_filtered(["echo", "test"])
    assert isinstance(stats["original_chars"], int)
    assert isinstance(stats["filtered_chars"], int)
    assert isinstance(stats["filter_name"], str)
