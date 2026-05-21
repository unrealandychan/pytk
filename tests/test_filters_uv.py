from pytk.filters.uv import UvFilter

def test_matches_uv():
    f = UvFilter()
    assert f.matches(['uv', 'run', 'pytest'])
    assert f.matches(['uv', 'pip', 'install', 'requests'])
    assert f.matches(['uv', 'sync'])
    assert not f.matches(['pip', 'install'])

def test_uv_run_pytest_dispatches_to_test_filter():
    f = UvFilter()
    output = 'tests/test_foo.py::test_bar PASSED\ntests/test_foo.py::test_baz PASSED\n===== 2 passed in 0.1s =====\n'
    result = f.filter(output, ['uv', 'run', 'pytest', 'tests/'])
    assert 'PASSED' not in result
    assert 'passed' in result

def test_uv_run_python_pytest_dispatches():
    f = UvFilter()
    output = 'tests/test_foo.py::test_bar PASSED\n===== 1 passed in 0.1s =====\n'
    result = f.filter(output, ['uv', 'run', 'python', '-m', 'pytest', 'tests/'])
    assert 'PASSED' not in result
    assert 'passed' in result

def test_uv_pip_install_filters_resolved():
    f = UvFilter()
    output = 'Resolved 15 packages in 0.5s\nInstalled 3 packages in 0.2s\n + requests==2.31.0\n + certifi==2023.1\n + urllib3==2.0.0\n'
    result = f.filter(output, ['uv', 'pip', 'install', 'requests'])
    assert len(result) < len(output)

def test_uv_sync_filters():
    f = UvFilter()
    output = 'Resolved 20 packages in 1.0s\nAudited 20 packages in 0.1s\n'
    result = f.filter(output, ['uv', 'sync'])
    assert result  # should return something
