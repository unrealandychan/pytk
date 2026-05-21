from pytk.filters.poetry import PoetryFilter


def test_poetry_matches():
    f = PoetryFilter()
    assert f.matches(['poetry', 'install'])
    assert f.matches(['poetry', 'run', 'pytest'])
    assert not f.matches(['pip', 'install'])
    assert not f.matches([])


def test_poetry_install_filters():
    f = PoetryFilter()
    output = (
        "Updating dependencies\n"
        "Resolving dependencies... (1.5s)\n"
        "\n"
        "Package operations: 3 installs, 0 updates, 0 removals\n"
        "\n"
        "  • Installing certifi (2023.7.22)\n"
        "  • Installing charset-normalizer (3.3.1)\n"
        "  • Installing requests (2.31.0)\n"
        "\n"
        "Writing lock file\n"
    )
    result = f.filter(output, ['poetry', 'install'])
    assert 'Package operations' in result
    assert 'Installing' in result
    assert 'Resolving' not in result


def test_poetry_install_fallback_when_no_match():
    f = PoetryFilter()
    output = "All packages are up to date."
    result = f.filter(output, ['poetry', 'install'])
    assert 'up to date' in result


def test_poetry_run_dispatches_to_inner_filter():
    f = PoetryFilter()
    # poetry run pytest — should dispatch to TestFilter
    output = "collected 5 items\n\ntest_foo.py .....   [100%]\n\n5 passed in 0.1s\n"
    result = f.filter(output, ['poetry', 'run', 'pytest'])
    # TestFilter should process it (keeps summary lines)
    assert '5 passed' in result


def test_poetry_run_unknown_inner_returns_output():
    f = PoetryFilter()
    output = "hello from myscript\n"
    result = f.filter(output, ['poetry', 'run', 'myscript'])
    assert 'hello from myscript' in result
