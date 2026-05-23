---
slug: testing
title: "Testing"
section: development
tags: [testing, development]
pin: false
importance: 66
created_at: 2026-05-23T04:42:01Z
rekipedia_version: 0.17.15
---

# Testing

## Summary

The test suite is organized as a set of focused unit and integration-style checks around the main runtime surfaces in `src/pytk/`. It covers configuration loading, cache behavior, CLI commands, shell hook generation, the command runner, filter routing, and per-filter output reduction logic. The broad pattern is: each production module has a corresponding `tests/test_*.py` file, and each filter module generally has its own dedicated test file validating both matching logic and output shaping.

The canonical way to run the suite is with `pytest` from the repository root:

```bash
pytest
```

That is the only test command explicitly surfaced in the analysis data, so it should be treated as the default entrypoint for local verification.

## Test Areas and Coverage Map

The table below maps major test areas to the modules or behaviors they exercise.

| Test area | Test file(s) | Modules / behaviors covered |
|---|---|---|
| ANSI stripping | `tests/test_ansi_stripping.py` | `src/pytk/filters/base.py` via [`strip_ansi`](src/pytk/filters/base.py#L8) and filter-specific output cleanup for git, pytest, and grep outputs |
| Cache semantics | `tests/test_cache.py` | `src/pytk/cache.py` via [`is_cacheable`](src/pytk/cache.py#L10), [`get`](src/pytk/cache.py#L15), [`set`](src/pytk/cache.py#L25), [`clear`](src/pytk/cache.py#L29), [`size`](src/pytk/cache.py#L33) |
| CLI surface | `tests/test_cli.py` | `src/pytk/cli.py` command entrypoints and output helpers, including [`main`](src/pytk/cli.py#L185), [`gain`](src/pytk/cli.py#L207), [`init_cmd`](src/pytk/cli.py#L538), [`passthrough`](src/pytk/cli.py#L596) |
| Config loading and precedence | `tests/test_config.py` | `src/pytk/config.py` via [`load_config`](src/pytk/config.py#L47), [`_deep_merge`](src/pytk/config.py#L37), [`_find_project_config`](src/pytk/config.py#L28), [`get_filter_config`](src/pytk/config.py#L66) |
| Doctor / environment checks | `tests/test_doctor.py` | `src/pytk/doctor.py` via [`run_doctor`](src/pytk/doctor.py#L28) and its status output helpers |
| Dry-run behavior | `tests/test_dry_run.py` | `src/pytk/runner.py` via [`run_filtered`](src/pytk/runner.py#L31), especially output prefixing and stats suppression |
| Cargo filter behavior | `tests/test_filters_cargo.py` | `src/pytk/filters/cargo.py` via [`CargoFilter`](src/pytk/filters/cargo.py#L5), [`matches`](src/pytk/filters/cargo.py#L6), and specialized builders for `build`, `test`, `clippy`, `add/update`, and `run` |
| `cat` filter behavior | `tests/test_filters_cat.py` | `src/pytk/filters/cat.py` via [`CatFilter`](src/pytk/filters/cat.py#L9) |
| `curl` / `wget` / HTTPie behavior | `tests/test_filters_curl.py` | `src/pytk/filters/curl.py` via [`CurlFilter`](src/pytk/filters/curl.py#L6), including verbose TLS cleanup, JSON truncation, and progress stripping |
| Docker filter behavior | `tests/test_filters_docker.py` | `src/pytk/filters/docker.py` via [`DockerFilter`](src/pytk/filters/docker.py#L6), covering `ps`, `images`, `logs`, `build`, `compose`, and `inspect` |
| Git filter behavior | `tests/test_filters_git.py` | `src/pytk/filters/git.py` via [`GitFilter`](src/pytk/filters/git.py#L5), including `status`, `diff`, `log`, and action compression |
| Grep filter behavior | `tests/test_filters_grep.py` | `src/pytk/filters/grep.py` via [`GrepFilter`](src/pytk/filters/grep.py#L10), including match grouping, max match handling, and binary output stripping |
| Kubectl filter behavior | `tests/test_filters_kubectl.py` | `src/pytk/filters/kubectl.py` via [`KubectlFilter`](src/pytk/filters/kubectl.py#L6), including `get`, `describe`, `logs`, `events`, `apply`, and `rollout` |
| Lint filter behavior | `tests/test_filters_lint.py` | `src/pytk/filters/lint.py` via [`LintFilter`](src/pytk/filters/lint.py#L5), covering `ruff`, `mypy`, `flake8`, `pylint`, and `tsc` |
| `ls` / `find` filter behavior | `tests/test_filters_ls.py` | `src/pytk/filters/ls.py` via [`LsFilter`](src/pytk/filters/ls.py#L7) |
| Newer filters | `tests/test_filters_new.py` | `src/pytk/filters/make.py`, `src/pytk/filters/terraform.py`, `src/pytk/filters/package_manager.py` |
| npm / yarn / pnpm / npx behavior | `tests/test_filters_npm.py` | `src/pytk/filters/npm.py` via [`NpmFilter`](src/pytk/filters/npm.py#L5) |
| Poetry behavior | `tests/test_filters_poetry.py` | `src/pytk/filters/poetry.py` via [`PoetryFilter`](src/pytk/filters/poetry.py#L5) |
| Pytest behavior | `tests/test_filters_test.py` | `src/pytk/filters/test.py` via [`TestFilter`](src/pytk/filters/test.py#L7) |
| uv behavior | `tests/test_filters_uv.py` | `src/pytk/filters/uv.py` via [`UvFilter`](src/pytk/filters/uv.py#L5) and dispatch into test/package-manager filters |
| Gain report export | `tests/test_gain_export.py` | `src/pytk/cli.py` gain output formatting, including JSON, CSV, Markdown, and date filtering |
| Shell hook management | `tests/test_hook.py` | `src/pytk/hook.py` via [`enable_hook`](src/pytk/hook.py#L90), [`disable_hook`](src/pytk/hook.py#L109), [`hook_status`](src/pytk/hook.py#L128) |
| Claude hook rewrite logic | `tests/test_hooks.py` | `src/pytk/hooks/claude_hook.py` via [`should_rewrite`](src/pytk/hooks/claude_hook.py#L25), [`rewrite_command`](src/pytk/hooks/claude_hook.py#L38), and [`main`](src/pytk/hooks/claude_hook.py#L43) |
| Agent init flows | `tests/test_init_agents.py` | CLI initialization helpers in `src/pytk/cli.py`, especially agent setup/install behavior |
| Command routing | `tests/test_runner.py` | `src/pytk/filters/registry.py` via [`get_filter`](src/pytk/filters/registry.py#L22) and routing decisions for git/pytest/ls/grep/cat |
| Runner execution | `tests/test_runner_run.py` | `src/pytk/runner.py` via [`run`](src/pytk/runner.py#L15) and [`run_filtered`](src/pytk/runner.py#L31) |

## How the Suite Is Structured

The suite is intentionally file-oriented: each `tests/test_*.py` file clusters assertions around a single subsystem or one closely related set of behaviors. For example, `tests/test_runner.py` focuses on filter selection, while `tests/test_runner_run.py` focuses on actual command execution and stats collection. Likewise, `tests/test_filters_new.py` groups the newer or more specialized filters together instead of splitting them into one file per module.

This structure makes it easy to run the whole suite with `pytest`, or to narrow down to a specific module while iterating on a feature. Common examples:

```bash
pytest tests/test_cache.py
pytest tests/test_filters_git.py
pytest tests/test_runner_run.py
```

A few notable organization patterns are visible from the test names:

- **Behavior-first naming**: tests are named after observable behavior, such as `test_git_status_strips_hints` or `test_dry_run_no_stats_update`.
- **Module-local fixtures**: some files define helper fixtures or helper functions to keep test data close to the assertions, such as `clear_cache` in `tests/test_cache.py` and `invoke_doctor` in `tests/test_doctor.py`.
- **Grouped variants**: filter tests often exercise both the matching predicate and multiple output shapes for different subcommands or command variants.

> **Sources:** `tests/test_ansi_stripping.py` · `tests/test_cache.py` · `tests/test_cli.py` · `tests/test_config.py` · `tests/test_doctor.py` · `tests/test_dry_run.py` · `tests/test_filters_*.py` · `tests/test_gain_export.py` · `tests/test_hook.py` · `tests/test_hooks.py` · `tests/test_init_agents.py` · `tests/test_runner.py` · `tests/test_runner_run.py`

## Canonical Test Command(s)

The canonical command is:

```bash
pytest
```

Run it from the repository root so `pytest` can discover the `tests/` directory and resolve the local package under `src/`.

If you need to target a single area, use the test file path directly:

```bash
pytest tests/test_config.py
pytest tests/test_filters_lint.py
pytest tests/test_hook.py
```

For focused debugging, `pytest` also supports selecting individual tests by name:

```bash
pytest tests/test_filters_git.py -k status
pytest tests/test_gain_export.py -k markdown
```

The analysis data does not show any additional wrapper scripts, tox environments, or custom test runners, so `pytest` should be considered the source of truth for test execution.

> **Sources:** `tests/test_ansi_stripping.py` · `tests/test_cache.py` · `tests/test_cli.py` · `tests/test_config.py` · `tests/test_doctor.py` · `tests/test_dry_run.py` · `tests/test_filters_cargo.py` · `tests/test_filters_cat.py` · `tests/test_filters_curl.py` · `tests/test_filters_docker.py` · `tests/test_filters_git.py` · `tests/test_filters_grep.py` · `tests/test_filters_kubectl.py` · `tests/test_filters_lint.py` · `tests/test_filters_ls.py` · `tests/test_filters_new.py` · `tests/test_filters_npm.py` · `tests/test_filters_poetry.py` · `tests/test_filters_test.py` · `tests/test_filters_uv.py` · `tests/test_gain_export.py` · `tests/test_hook.py` · `tests/test_hooks.py` · `tests/test_init_agents.py` · `tests/test_runner.py` · `tests/test_runner_run.py`

## Coverage Notes

Based on the available test inventory, the suite gives strongest coverage to:

- **Filter-specific compression logic** across many command families
- **CLI output and option handling**
- **Configuration precedence and file discovery**
- **Shell-hook installation and command rewriting**
- **Runner behavior, including stats and dry-run semantics**

There are also explicit tests for utility-level concerns like ANSI stripping and cache TTL behavior, which suggests the project treats output minimization and reproducibility as first-class concerns rather than incidental implementation details.

What is not visible from the analysis data is any measure of coverage percentage, parametrized test matrix size, or tooling-specific configuration such as `pytest.ini` options. So the documentation should treat the suite as well-partitioned and behavior-driven, but not claim any exact coverage percentage.

> **Sources:** `tests/test_cache.py` · `tests/test_dry_run.py` · `tests/test_filters_ansi_stripping.py`?