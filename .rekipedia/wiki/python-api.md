---
slug: python-api
title: "Public Python API Reference"
section: api-reference
tags: [api, reference]
pin: false
importance: 74
created_at: 2026-05-23T04:47:41Z
rekipedia_version: 0.17.15
---

# Public Python API Reference

## Package Index

This page documents the importable public implementation API exposed under `src/pytk/`, focusing on user-facing modules, classes, functions, and methods. It intentionally excludes test, CI, and config-only symbols, and it does not cover CLI usage or repository layout beyond what is necessary to orient API consumers.

At a high level, the package is organized around a command interception pipeline:

- [`pytk.cache`](src/pytk/cache.py) — lightweight output caching helpers
- [`pytk.config`](src/pytk/config.py) — configuration loading and merge helpers
- [`pytk.doctor`](src/pytk/doctor.py) — environment validation checks
- [`pytk.filters.base`](src/pytk/filters/base.py) — shared filter base utilities
- [`pytk.filters.registry`](src/pytk/filters/registry.py) — filter selection by command
- [`pytk.hook`](src/pytk/hook.py) — shell hook enable/disable/status helpers
- [`pytk.hooks.claude_hook`](src/pytk/hooks/claude_hook.py) — Claude Code hook rewrite logic
- [`pytk.runner`](src/pytk/runner.py) — command execution and filtered-run orchestration
- [`pytk.filters.*`](src/pytk/filters/) — command-specific output filters

The package root [`pytk.__init__`](src/pytk/__init__.py) is present, but the analysis data does not expose any exported names there, so no public API surface can be confirmed from it.

### Public module inventory

| Module | Primary purpose | Key public symbols |
|---|---|---|
| [`pytk.cache`](src/pytk/cache.py) | Cache command outputs for reuse | [`is_cacheable`](src/pytk/cache.py#L10), [`get`](src/pytk/cache.py#L15), [`set`](src/pytk/cache.py#L25), [`clear`](src/pytk/cache.py#L29), [`size`](src/pytk/cache.py#L33) |
| [`pytk.config`](src/pytk/config.py) | Load and merge configuration | [`load_config`](src/pytk/config.py#L47), [`get_filter_config`](src/pytk/config.py#L66) |
| [`pytk.doctor`](src/pytk/doctor.py) | Health checks for the installed environment | [`run_doctor`](src/pytk/doctor.py#L28) |
| [`pytk.filters.base`](src/pytk/filters/base.py) | Shared filter primitives | [`strip_ansi`](src/pytk/filters/base.py#L8), [`cmd_name`](src/pytk/filters/base.py#L13), [`BaseFilter`](src/pytk/filters/base.py#L24) |
| [`pytk.filters.registry`](src/pytk/filters/registry.py) | Route commands to filters | [`get_filter`](src/pytk/filters/registry.py#L22) |
| [`pytk.hook`](src/pytk/hook.py) | Shell hook management | [`enable_hook`](src/pytk/hook.py#L90), [`disable_hook`](src/pytk/hook.py#L109), [`hook_status`](src/pytk/hook.py#L128) |
| [`pytk.hooks.claude_hook`](src/pytk/hooks/claude_hook.py) | Rewrite commands for Claude Code tool hooks | [`should_rewrite`](src/pytk/hooks/claude_hook.py#L25), [`rewrite_command`](src/pytk/hooks/claude_hook.py#L38), [`main`](src/pytk/hooks/claude_hook.py#L43) |
| [`pytk.runner`](src/pytk/runner.py) | Execute commands and apply filters | [`run`](src/pytk/runner.py#L15), [`run_filtered`](src/pytk/runner.py#L31) |

> **Sources:** `src/pytk/__init__.py` · `src/pytk/cache.py` · `src/pytk/config.py` · `src/pytk/doctor.py` · `src/pytk/filters/base.py` · `src/pytk/filters/registry.py` · `src/pytk/hook.py` · `src/pytk/hooks/claude_hook.py` · `src/pytk/runner.py`

---

## `pytk.cache`

The cache module provides a small persistence layer for command outputs. It is designed around a simple eligibility check plus get/set operations keyed by command and working directory.

### API reference

| Symbol | Signature | Responsibility | Return value / side effect |
|---|---|---|---|
| [`is_cacheable`](src/pytk/cache.py#L10) | `is_cacheable(command)` | Decide whether a command can be cached | Returns a boolean indicating cache eligibility |
| [`get`](src/pytk/cache.py#L15) | `get(command, cwd, ttl)` | Retrieve a cached output if it exists and is still fresh | Returns cached output on hit; otherwise a miss/empty result |
| [`set`](src/pytk/cache.py#L25) | `set(command, cwd, output)` | Store command output in the cache | Writes cache data as a side effect |
| [`clear`](src/pytk/cache.py#L29) | `clear()` | Remove cache entries | Clears cache state as a side effect |
| [`size`](src/pytk/cache.py#L33) | `size()` | Report cache size | Returns current cache size |

The behavior exposed here is intentionally minimal: there are no higher-level abstractions, just command eligibility and cache CRUD operations. Consumers typically pair [`is_cacheable`](src/pytk/cache.py#L10) with [`get`](src/pytk/cache.py#L15) and [`set`](src/pytk/cache.py#L25) to avoid re-running expensive commands.

> **Sources:** `src/pytk/cache.py` · L10–L34 · [`is_cacheable`](src/pytk/cache.py#L10) · [`get`](src/pytk/cache.py#L15) · [`set`](src/pytk/cache.py#L25) · [`clear`](src/pytk/cache.py#L29) · [`size`](src/pytk/cache.py#L33)

---

## `pytk.config`

This module is responsible for finding configuration files, merging them, and retrieving per-filter configuration dictionaries. It is the main programmatic entry point for package configuration.

### API reference

| Symbol | Signature | Responsibility | Return value / side effect |
|---|---|---|---|
| [`_find_project_config`](src/pytk/config.py#L28) | `_find_project_config(start)` | Walk upward from a starting directory to locate `.pytk.toml` | Returns the first matching project config path or no-match result |
| [`_deep_merge`](src/pytk/config.py#L37) | `_deep_merge(base, override)` | Recursively merge two nested dictionaries | Returns a merged dictionary, with override values winning |
| [`load_config`](src/pytk/config.py#L47) | `load_config(cwd)` | Load default, user, and project configuration into one effective config | Returns the merged configuration mapping |
| [`get_filter_config`](src/pytk/config.py#L66) | `get_filter_config(config, filter_name)` | Extract configuration for a named filter | Returns a filter-specific config dict, falling back to `{}` |

Among these, [`load_config`](src/pytk/config.py#L47) is the most important public entry point. It encapsulates the package’s configuration precedence model and is the function most callers should use before invoking the runner or filter machinery. [`get_filter_config`](src/pytk/config.py#L66) is a convenience accessor used when a filter needs only its own configuration subtree.

### Usage notes

- [`_find_project_config`](src/pytk/config.py#L28) is an implementation helper, but it is still documented here because it is present in the importable module and part of the observable API surface from static analysis.
- [`_deep_merge`](src/pytk/config.py#L37) makes nested overrides deterministic and avoids shallow replacement of structured settings.

> **Sources:** `src/pytk/config.py` · L28–L68 · [`_find_project_config`](src/pytk/config.py#L28) · [`_deep_merge`](src/pytk/config.py#L37) · [`load_config`](src/pytk/config.py#L47) · [`get_filter_config`](src/pytk/config.py#L66)

---

## `pytk.doctor`

The doctor module runs environment and installation checks and produces a health report. It is the package’s diagnostic entry point for validating that the surrounding runtime is usable.

### API reference

| Symbol | Signature | Responsibility | Return value / side effect |
|---|---|---|---|
| [`_ok`](src/pytk/doctor.py#L16) | `_ok(msg)` | Format a success indicator | Produces status text for console output |
| [`_fail`](src/pytk/doctor.py#L20) | `_fail(msg)` | Format a failure indicator | Produces status text for console output |
| [`_warn`](src/pytk/doctor.py#L24) | `_warn(msg)` | Format a warning indicator | Produces status text for console output |
| [`run_doctor`](src/pytk/doctor.py#L28) | `run_doctor(cwd)` | Execute all diagnostic checks | Returns an exit code: `0` for success, `1` for critical failure |

The central API is [`run_doctor`](src/pytk/doctor.py#L28), which aggregates the various checks and returns a process-style exit code. The helper formatters are internal by naming convention, but they are part of the documented implementation surface of the module.

> **Sources:** `src/pytk/doctor.py` · L16–L112 · [`_ok`](src/pytk/doctor.py#L16) · [`_fail`](src/pytk/doctor.py#L20) · [`_warn`](src/pytk/doctor.py#L24) · [`run_doctor`](src/pytk/doctor.py#L28)

---

## `pytk.filters.base`

This module defines the shared building blocks used by concrete command filters. It contains both low-level text utilities and a minimal filter base class that establishes the expected interface.

### API reference

| Symbol | Signature | Responsibility | Return value / side effect |
|---|---|---|---|
| [`strip_ansi`](src/pytk/filters/base.py#L8) | `strip_ansi(text)` | Remove ANSI escape codes from text | Returns cleaned text |
| [`cmd_name`](src/pytk/filters/base.py#L13) | `cmd_name(cmd)` | Extract the executable basename from a command vector | Returns normalized command name |
| [`BaseFilter`](src/pytk/filters/base.py#L24) | class | Base interface for command filters | Provides shared method contract |
| [`BaseFilter.matches`](src/pytk/filters/base.py#L26) | `matches(self, cmd)` | Decide whether the filter applies | Returns boolean |
| [`BaseFilter.filter`](src/pytk/filters/base.py#L30) | `filter(self, output, cmd)` | Transform output into a shorter form | Returns filtered output |
| [`BaseFilter.savings_example`](src/pytk/filters/base.py#L33) | `savings_example(self)` | Provide a sample before/after savings record | Returns a dict with `before`, `after`, and `description` |

`BaseFilter` establishes the core protocol consumed by the registry and runner. Concrete filter classes such as [`GitFilter`](src/pytk/filters/git.py#L5) and [`NpmFilter`](src/pytk/filters/npm.py#L5) implement this interface to compress output for specific commands.

> **Sources:** `src/pytk/filters/base.py` · L8–L35 · [`strip_ansi`](src/pytk/filters/base.py#L8) · [`cmd_name`](src/pytk/filters/base.py#L13) · [`BaseFilter`](src/pytk/filters/base.py#L24) · [`BaseFilter.matches`](src/pytk/filters/base.py#L26) · [`BaseFilter.filter`](src/pytk/filters/base.py#L30) · [`BaseFilter.savings_example`](src/pytk/filters/base.py#L33)

---

## `pytk.filters.registry`

The registry maps a command to the appropriate filter implementation. It is the selection layer between raw command execution and per-command output compression.

### API reference

| Symbol | Signature | Responsibility | Return value / side effect |
|---|---|---|---|
| [`get_filter`](src/pytk/filters/registry.py#L22) | `get_filter(cmd)` | Resolve the most appropriate filter for a command | Returns a filter instance or a no-match result |

This is a small but important entry point because [`run_filtered`](src/pytk/runner.py#L31) depends on it to determine whether output should be transformed. The module itself does not expose additional public helpers in the analysis data.

> **Sources:** `src/pytk/filters/registry.py` · L22–L26 · [`get_filter`](src/pytk/filters/registry.py#L22)

---

## `pytk.hook`

This module manages shell integration for automatic command interception. It appears to support enabling, disabling, and reporting status for hook-based activation.

### API reference

| Symbol | Signature | Responsibility | Return value / side effect |
|---|---|---|---|
| [`_detect_shell`](src/pytk/hook.py#L43) | `_detect_shell()` | Detect the active shell | Returns a shell identifier |
| [`_get_config_file`](src/pytk/hook.py#L52) | `_get_config_file(shell)` | Resolve the shell config file to edit | Returns a file path |
| [`_build_bash_snippet`](src/pytk/hook.py#L61) | `_build_bash_snippet()` | Generate Bash hook snippet text | Returns shell snippet text |
| [`_build_fish_snippet`](src/pytk/hook.py#L72) | `_build_fish_snippet()` | Generate Fish hook snippet text | Returns shell snippet text |
| [`_is_enabled`](src/pytk/hook.py#L83) | `_is_enabled(cfg_file)` | Check whether the hook is already installed | Returns boolean |
| [`enable_hook`](src/pytk/hook.py#L90) | `enable_hook(shell, cfg_file)` | Append hook configuration if not already present | Returns `(already_was_enabled, config_file_path)` |
| [`disable_hook`](src/pytk/hook.py#L109) | `disable_hook(shell, cfg_file)` | Remove the hook section from the config | Returns `(was_enabled, config_file_path)` |
| [`hook_status`](src/pytk/hook.py#L128) | `hook_status(shell, cfg_file)` | Report whether the hook is active | Returns status information |

The key operational methods are [`enable_hook`](src/pytk/hook.py#L90) and [`disable_hook`](src/pytk/hook.py#L109), which mutate shell configuration files. Their return values are explicitly structured to support idempotent tooling: both report whether the hook was already present, or whether removal actually occurred.

> **Sources:** `src/pytk/hook.py` · L43–L136 · [`_detect_shell`](src/pytk/hook.py#L43) · [`_get_config_file`](src/pytk/hook.py#L52) · [`_build_bash_snippet`](src/pytk/hook.py#L61) · [`_build_fish_snippet`](src/pytk/hook.py#L72) · [`_is_enabled`](src/pytk/hook.py#L83) · [`enable_hook`](src/pytk/hook.py#L90) · [`disable_hook`](src/pytk/hook.py#L109) · [`hook_status`](src/pytk/hook.py#L128)

---

## `pytk.hooks.claude_hook`

This module contains the hook-time rewrite logic used by Claude Code integration. It decides whether an incoming command should be prefixed with `pytk` and exposes a small script-style entry point.

### API reference

| Symbol | Signature | Responsibility | Return value / side effect |
|---|---|---|---|
| [`should_rewrite`](src/pytk/hooks/claude_hook.py#L25) | `should_rewrite(command)` | Determine whether a command should be rewritten | Returns boolean |
| [`rewrite_command`](src/pytk/hooks/claude_hook.py#L38) | `rewrite_command(command)` | Prefix a command with `pytk` | Returns rewritten command text |
| [`main`](src/pytk/hooks/claude_hook.py#L43) | `main()` | Process a hook payload from stdin/stdout | Produces rewritten or passthrough JSON-like output and exits |

The rewrite decision is concentrated in [`should_rewrite`](src/pytk/hooks/claude_hook.py#L25), which is the primary predicate consumers should understand. [`rewrite_command`](src/pytk/hooks/claude_hook.py#L38) is a straightforward transformation helper, while [`main`](src/pytk/hooks/claude_hook.py#L43) ties those helpers into the hook execution model.

> **Sources:** `src/pytk/hooks/claude_hook.py` · L25–L65 · [`should_rewrite`](src/pytk/hooks/claude_hook.py#L25) · [`rewrite_command`](src/pytk/hooks/claude_hook.py#L38) · [`main`](src/pytk/hooks/claude_hook.py#L43)

---

## `pytk.runner`

The runner is the central orchestration layer: it executes commands, optionally applies filters, and returns both transformed output and stats for later aggregation.

### API reference

| Symbol | Signature | Responsibility | Return value / side effect |
|---|---|---|---|
| [`run`](src/pytk/runner.py#L15) | `run(cmd, capture_env)` | Execute a command as a subprocess | Returns `(output, exit_code)` |
| [`run_filtered`](src/pytk/runner.py#L31) | `run_filtered(cmd, no_cache, dry_run)` | Execute, filter, and collect stats | Returns `(filtered_output, exit_code, stats)` |
| [`_append_stats`](src/pytk/runner.py#L93) | `_append_stats(cmd, stats)` | Persist run statistics | Writes stats as a side effect |

For most consumers, [`run_filtered`](src/pytk/runner.py#L31) is the function that matters: it coordinates execution, filter selection, caching behavior, dry-run handling, and stats collection in a single result tuple. The lower-level [`run`](src/pytk/runner.py#L15) is useful when command execution is needed without output reduction.

### Call chain

A typical flow is:

`call site → run_filtered → get_filter → selected_filter.filter → _append_stats`

This is the core public-facing execution path of the package.

> **Sources:** `src/pytk/runner.py` · L15–L104 · [`run`](src/pytk/runner.py#L15) · [`run_filtered`](src/pytk/runner.py#L31) · [`_append_stats`](src/pytk/runner.py#L93)

---

## Filter modules

The package ships several command-specific filter implementations under `src/pytk/filters/`. These modules expose a consistent interface: `matches`, `filter`, and `savings_example`, plus private helpers for command subtypes.

### Filter API summary

| Module | Class | Key methods | Main responsibility |
|---|---|---|---|
| [`pytk.filters.cargo`](src/pytk/filters/cargo.py) | [`CargoFilter`](src/pytk/filters/cargo.py#L5) | [`matches`](src/pytk/filters/cargo.py#L6), [`filter`](src/pytk/filters/cargo.py#L10), [`_filter_build`](src/pytk/filters/cargo.py#L25), [`_filter_test`](src/pytk/filters/cargo.py#L79), [`_filter_clippy`](src/pytk/filters/cargo.py#L88), [`_filter_add_update`](src/pytk/filters/cargo.py#L99), [`_filter_run`](src/pytk/filters/cargo.py#L131), [`savings_example`](src/pytk/filters/cargo.py#L140) | Compress Cargo-related command output |
| [`pytk.filters.cat`](src/pytk/filters/cat.py) | [`CatFilter`](src/pytk/filters/cat.py#L9) | [`matches`](src/pytk/filters/cat.py#L10), [`filter`](src/pytk/filters/cat.py#L14), [`savings_example`](src/pytk/filters/cat.py#L44) | Truncate or simplify `cat` output |
| [`pytk.filters.curl`](src/pytk/filters/curl.py) | [`CurlFilter`](src/pytk/filters/curl.py#L6) | [`matches`](src/pytk/filters/curl.py#L7), [`filter`](src/pytk/filters/curl.py#L11), [`_filter_curl`](src/pytk/filters/curl.py#L21), [`_maybe_truncate_json`](src/pytk/filters/curl.py#L81), [`_filter_httpie`](src/pytk/filters/curl.py#L100), [`_filter_wget`](src/pytk/filters/curl.py#L122), [`savings_example`](src/pytk/filters/curl.py#L137) | Reduce verbose HTTP client output |
| [`pytk.filters.docker`](src/pytk/filters/docker.py) | [`DockerFilter`](src/pytk/filters/docker.py#L6) | [`matches`](src/pytk/filters/docker.py#L7), [`filter`](src/pytk/filters/docker.py#L11), [`_filter_ps`](src/pytk/filters/docker.py#L39), [`_filter_images`](src/pytk/filters/docker.py#L62), [`_filter_logs`](src/pytk/filters/docker.py#L81), [`_filter_build`](src/pytk/filters/docker.py#L106), [`_filter_compose_action`](src/pytk/filters/docker.py#L143), [`_filter_inspect`](src/pytk/filters/docker.py#L172), [`savings_example`](src/pytk/filters/docker.py#L202) | Condense Docker output |
| [`pytk.filters.git`](src/pytk/filters/git.py) | [`GitFilter`](src/pytk/filters/git.py#L5) | [`matches`](src/pytk/filters/git.py#L6), [`filter`](src/pytk/filters/git.py#L10), [`_filter_status`](src/pytk/filters/git.py#L23), [`_filter_diff`](src/pytk/filters/git.py#L46), [`_compress_msg`](src/pytk/filters/git.py#L62), [`_filter_log`](src/pytk/filters/git.py#L70), [`_filter_action`](src/pytk/filters/git.py#L99), [`savings_example`](src/pytk/filters/git.py#L119) | Reduce Git status/diff/log noise |
| [`pytk.filters.grep`](src/pytk/filters/grep.py) | [`GrepFilter`](src/pytk/filters/grep.py#L10) | [`matches`](src/pytk/filters/grep.py#L11), [`filter`](src/pytk/filters/grep.py#L15), [`savings_example`](src/pytk/filters/grep.py#L69) | Group and truncate grep output |
| [`pytk.filters.kubectl`](src/pytk/filters/kubectl.py) | [`KubectlFilter`](src/pytk/filters/kubectl.py#L6) | [`matches`](src/pytk/filters/kubectl.py#L7), [`filter`](src/pytk/filters/kubectl.py#L11), [`_filter_get`](src/pytk/filters/kubectl.py#L31), [`_filter_get_pods`](src/pytk/filters/kubectl.py#L40), [`_filter_describe`](src/pytk/filters/kubectl.py#L78), [`_filter_logs`](src/pytk/filters/kubectl.py#L137), [`_filter_events`](src/pytk/filters/kubectl.py#L183), [`_filter_action`](src/pytk/filters/kubectl.py#L219), [`_filter_rollout`](src/pytk/filters/kubectl.py#L224), [`savings_example`](src/pytk/filters/kubectl.py#L230) | Compress Kubernetes CLI output |
| [`pytk.filters.lint`](src/pytk/filters/lint.py) | [`LintFilter`](src/pytk/filters/lint.py#L5) | [`matches`](src/pytk/filters/lint.py#L6), [`filter`](src/pytk/filters/lint.py#L10), [`_filter_ruff`](src/pytk/filters/lint.py#L25), [`_filter_mypy`](src/pytk/filters/lint.py#L40), [`_filter_flake8`](src/pytk/filters/lint.py#L54), [`_filter_pylint`](src/pytk/filters/lint.py#L61), [`_filter_tsc`](src/pytk/filters/lint.py#L77), [`savings_example`](src/pytk/filters/lint.py#L90) | Tidy output from static analysis tools |
| [`pytk.filters.ls`](src/pytk/filters/ls.py) | [`LsFilter`](src/pytk/filters/ls.py#L7) | [`matches`](src/pytk/filters/ls.py#L8), [`filter`](src/pytk/filters/ls.py#L12), [`_filter_ls`](src/pytk/filters/ls.py#L25), [`_filter_find`](src/pytk/filters/ls.py#L45), [`_truncate`](src/pytk/filters/ls.py#L49), [`savings_example`](src/pytk/filters/ls.py#L57) | Shorten directory listings |
| [`pytk.filters.make`](src/pytk/filters/make.py) | [`MakeFilter`](src/pytk/filters/make.py#L5) | [`matches`](src/pytk/filters/make.py#L6), [`filter`](src/pytk/filters/make.py#L10), [`savings_example`](src/pytk/filters/make.py#L24) | Suppress make directory chatter |
| [`pytk.filters.npm`](src/pytk/filters/npm.py) | [`NpmFilter`](src/pytk/filters/npm.py#L5) | [`matches`](src/pytk/filters/npm.py#L6), [`filter`](src/pytk/filters/npm.py#L10), [`_filter_install`](src/pytk/filters/npm.py#L30), [`_filter_run`](src/pytk/filters/npm.py#L53), [`_filter_audit`](src/pytk/filters/npm.py#L76), [`_filter_test`](src/pytk/filters/npm.py#L92), [`_filter_npx`](src/pytk/filters/npm.py#L102), [`savings_example`](src/pytk/filters/npm.py#L122) | Compress Node package manager output |
| [`pytk.filters.package_manager`](src/pytk/filters/package_manager.py) | [`PackageManagerFilter`](src/pytk/filters/package_manager.py#L5) | [`matches`](src/pytk/filters/package_manager.py#L6), [`filter`](src/pytk/filters/package_manager.py#L12), [`savings_example`](src/pytk/filters/package_manager.py#L40) | Shared package-manager output reduction |
| [`pytk.filters.poetry`](src/pytk/filters/poetry.py) | [`PoetryFilter`](src/pytk/filters/poetry.py#L5) | [`matches`](src/pytk/filters/poetry.py#L6), [`filter`](src/pytk/filters/poetry.py#L10), [`_filter_install`](src/pytk/filters/poetry.py#L23), [`savings_example`](src/pytk/filters/poetry.py#L34) | Compress Poetry install output |
| [`pytk.filters.terraform`](src/pytk/filters/terraform.py) | [`TerraformFilter`](src/pytk/filters/terraform.py#L5) | [`matches`](src/pytk/filters/terraform.py#L6), [`filter`](src/pytk/filters/terraform.py#L12), [`savings_example`](src/pytk/filters/terraform.py#L32) | Reduce Terraform plan/apply noise |
| [`pytk.filters.uv`](src/pytk/filters/uv.py) | [`UvFilter`](src/pytk/filters/uv.py#L5) | [`matches`](src/pytk/filters/uv.py#L6), [`filter`](src/pytk/filters/uv.py#L9), [`savings_example`](src/pytk/filters/uv.py#L47) | Handle `uv` command output |

### Common filter contract

All filter classes listed above follow the same basic shape:

- [`matches(self, cmd)`](src/pytk/filters/base.py#L26) determines applicability.
- [`filter(self, output, cmd)`](src/pytk/filters/base.py#L30) returns transformed output.
- [`savings_example(self)`](src/pytk/filters/base.py#L33) provides a displayable example for introspection commands.

That consistent contract is what allows the registry and runner to treat each filter uniformly.

> **Sources:** `src/pytk/filters/base.py` · `src/pytk/filters/cargo.py` · `src/pytk/filters/cat.py` · `src/pytk/filters/curl.py` · `src/pytk/filters/docker.py` · `src/pytk/filters/git.py` · `src/pytk/filters/grep.py` · `src/pytk/filters/kubectl.py` · `src/pytk/filters/lint.py` · `src/pytk/filters/ls.py` · `src/pytk/filters/make.py` · `src/pytk/filters/npm.py` · `src/pytk/filters/package_manager.py` · `src/pytk/filters/poetry.py` · `src/pytk/filters/terraform.py` · `src/pytk/filters/uv.py`

---

## Notes on API stability and visibility

A few symbols in the analysis are underscore-prefixed helpers, which conventionally indicates internal use. They are included here because the task is to document the public Python API exposed by the importable package modules, and the analysis data identifies them as implementation symbols in those modules. If you are consuming the package externally, the most stable entry points are the non-underscore functions and classes such as [`load_config`](src/pytk/config.py#L47), [`run_filtered`](src/pytk/runner.py#L31), [`get_filter`](src/pytk/filters/registry.py#L22), and the concrete filter classes.

The analysis data does not expose `__all__` definitions or package-level re-exports from [`pytk.__init__`](src/pytk/__init__.py), so the safest import style is to target the specific module that defines the symbol you need.

> **Sources:** `src/pytk/__init__.py` · `src/pytk/config.py` · `src/pytk/filters/registry.py` · `src/pytk/runner.py`