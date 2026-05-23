---
slug: installation-and-setup
title: "Getting Started: Install, Build, and Run from Source"
section: getting-started
tags: [getting-started, configuration]
pin: false
importance: 72
created_at: 2026-05-23T04:40:52Z
rekipedia_version: 0.17.15
---

# Getting Started: Install, Build, and Run from Source

This page documents the user-facing path to install `pytk-cli` from source, build release artifacts, and verify the command-line interface after installation. It focuses on setup and invocation only, using evidence from the project metadata, CLI entry points, and release/build configuration.

## Prerequisites

The repository’s packaging metadata identifies the project as a Python package named `pytk-cli` version `0.2.0`, with the primary console entry point exposed as `pytk = "pytk.cli:main"` in `pyproject.toml` evidence. That means a successful installation should provide a `pytk` command on your `PATH`. The build workflow also shows tag-based release publishing (`v*`), which is consistent with standard Python packaging and distribution flows.

At a minimum, you should have:

- A modern Python 3 interpreter and `pip`
- Access to a virtual environment tool such as `venv`
- The ability to install Python build tools (`build`, `twine`) when preparing release artifacts

Because the repository is source-based, the recommended workflow is to install into an isolated environment rather than system Python. While the analysis does not expose an explicit minimum Python version, the packaging layout and tests indicate a typical modern Python project structure.

A practical setup sequence is:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

> **Sources:** `pyproject.toml` · package evidence in repository metadata (`py_name: pytk-cli`, `py_version: 0.2.0`, `entry_points: pytk = "pytk.cli:main"`) · `src/pytk/cli.py#L125-L178` (`PytkGroup`) · `src/pytk/cli.py#L750-L753` (`hook_run_claude`)

## Editable / Local Installation

For development or testing from source, the standard editable install path is to install the project package into a local environment. The analysis does not show an explicit `pip install -e .` command in the repository files, but the package layout strongly implies that this is the intended local workflow because the CLI is defined as a console script and lives under `src/pytk`.

A typical editable installation would be:

```bash
pip install -e .
```

This makes the `pytk` command resolve directly from the working tree, so changes to `src/pytk/cli.py`, `src/pytk/runner.py`, `src/pytk/config.py`, or the filter modules become visible without rebuilding a wheel.

If you want to confirm the package metadata is being read correctly, you can also inspect the project config:

```bash
python -m pip show pytk-cli
```

A successful local install should make the console entry point available:

```bash
pytk --help
```

The repository tests explicitly cover CLI behaviors such as passthrough invocation, listing filters, and initialization flows, which gives confidence that the installed command should be usable immediately after installation.

> **Sources:** `pyproject.toml` metadata evidence (`py_name: pytk-cli`, `entry_points: pytk = "pytk.cli:main"`) · [`PytkGroup`](src/pytk/cli.py#L125-L178) · [`main`](src/pytk/hooks/claude_hook.py#L43-L65)

## Build and Release Commands

The repository’s documented build commands are minimal and use standard Python packaging tools:

| Command | Purpose | Expected outcome |
|---|---|---|
| `pip install build twine` | Install packaging tools needed for source distributions and wheels | `build` and `twine` become available in the environment |
| `python -m build` | Create distributable release artifacts from the source tree | Produces built package artifacts such as a wheel and source distribution under `dist/` |

These commands are enough for a user preparing a release or verifying that the source tree is buildable. The analysis does not expose an explicit `twine upload` command in the repo, so this page does not speculate about publishing beyond the fact that the GitHub workflow is triggered on version tags (`v*`).

A standard build flow looks like this:

```bash
python -m pip install --upgrade build twine
python -m build
```

After a successful build, you would normally inspect the generated distribution files before installation or publishing. The build artifacts matter to users only because they are the installable outputs: the wheel is what `pip install dist/*.whl` would consume, and the source distribution is what package managers and release tooling may validate.

> **Sources:** `build_commands` evidence (`pip install build twine`, `python -m build`) · `.github/workflows/publish.yml` evidence (`push` tags `v*`) · `pyproject.toml` package evidence

## Verifying the CLI After Installation

Once installed, the most direct verification is to invoke the `pytk` console command that the package exports. A healthy installation should respond to help and basic subcommands.

Recommended smoke tests:

```bash
pytk --help
pytk doctor
pytk list-filters
```

Expected outcomes:

- `pytk --help` prints usage information for the CLI and confirms the console entry point is installed.
- `pytk doctor` runs the environment check command implemented by [`doctor_cmd`](src/pytk/cli.py#L671-L676) and the underlying [`run_doctor`](src/pytk/doctor.py#L28-L112) routine.
- `pytk list-filters` confirms the installed CLI can enumerate supported filters via [`list_filters`](src/pytk/cli.py#L680-L702).

For a more complete functional check, you can run a command that should be intercepted by the tool’s passthrough or filter pipeline. The repository’s tests show that the CLI supports passthrough and command-specific handling, so a simple validation is:

```bash
pytk git status
```

If the tool is working correctly, it should execute without installation errors and produce output consistent with the installed command chain. The exact rewriting behavior depends on the command and is outside the scope of this page, but the important user-visible result is that the CLI runs and recognizes commands.

If you want to verify package metadata from the installation itself, the following can help:

```bash
python -m pip show pytk-cli
python -c "import pytk; print(pytk.__file__)"
```

These checks confirm that the package is importable and that the installed module resolves to the expected environment.

> **Sources:** [`doctor_cmd`](src/pytk/cli.py#L671-L676) · [`run_doctor`](src/pytk/doctor.py#L28-L112) · [`list_filters`](src/pytk/cli.py#L680-L702) · [`PytkGroup`](src/pytk/cli.py#L125-L178)

## Suggested Installation and Verification Workflow

A practical end-to-end workflow from a fresh clone is:

1. Create and activate a virtual environment.
2. Install editable dependencies from the source tree.
3. Build release artifacts if you need to validate packaging.
4. Run the CLI help and a couple of subcommands to confirm the install.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
python -m pip install --upgrade build twine
python -m build
pytk --help
pytk doctor
pytk list-filters
```

This sequence is intentionally conservative: it ensures the environment is isolated, the source tree is installed locally, the package can be built, and the resulting console entry point behaves as expected.

## Command Summary

| Command | When to use it | What success looks like |
|---|---|---|
| `python -m venv .venv` | Start a clean local environment | A new isolated Python environment exists |
| `pip install -e .` | Install the project from the checked-out source | `pytk` becomes available and reflects local code |
| `pip install build twine` | Prepare to create or inspect release artifacts | Build tools are installed successfully |
| `python -m build` | Produce release packages from source | Build completes and generates distributable artifacts |
| `pytk --help` | Verify the CLI entry point | Usage text is displayed |
| `pytk doctor` | Check the installation environment | Diagnostic output completes without install-time errors |
| `pytk list-filters` | Confirm installed command functionality | The available filters are listed |

> **Sources:** build commands evidence; package metadata evidence (`pytk = "pytk.cli:main"`, `py_name: pytk-cli`) · [`doctor_cmd`](src/pytk/cli.py#L671-L676) · [`list_filters`](src/pytk/cli.py#L680-L702)