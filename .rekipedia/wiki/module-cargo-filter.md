---
slug: module-cargo-filter
title: "Cargo command filter"
section: core-components
tags: [modules, reference]
pin: false
importance: 76
created_at: 2026-05-23T04:41:48Z
rekipedia_version: 0.17.15
---

# Cargo command filter

## Overview

[`CargoFilter`](src/pytk/filters/cargo.py#L5) is the Cargo-specific output compressor used by the filter registry. It follows the same interface as the other command filters in this repository: [`matches`](src/pytk/filters/cargo.py#L6) decides whether the filter applies, and [`filter`](src/pytk/filters/cargo.py#L10) rewrites command output into a shorter form. The implementation is intentionally narrow: it only handles the Cargo subcommands and output patterns that are visible in the code, and it delegates all other cases to pass through unchanged.

The filter’s behavior is organized around five helper methods:

- [`CargoFilter._filter_build`](src/pytk/filters/cargo.py#L25)
- [`CargoFilter._filter_test`](src/pytk/filters/cargo.py#L79)
- [`CargoFilter._filter_clippy`](src/pytk/filters/cargo.py#L88)
- [`CargoFilter._filter_add_update`](src/pytk/filters/cargo.py#L99)
- [`CargoFilter._filter_run`](src/pytk/filters/cargo.py#L131)

A compact savings sample is also provided by [`CargoFilter.savings_example`](src/pytk/filters/cargo.py#L140), which is used by `pytk list-filters` to display representative compression results.

> **Sources:** `src/pytk/filters/cargo.py` · L5–L145 · [`CargoFilter`](src/pytk/filters/cargo.py#L5) · [`CargoFilter.matches`](src/pytk/filters/cargo.py#L6) · [`CargoFilter.filter`](src/pytk/filters/cargo.py#L10) · [`CargoFilter.savings_example`](src/pytk/filters/cargo.py#L140)

## Supported Cargo subcommands

The match gate is very simple: [`CargoFilter.matches`](src/pytk/filters/cargo.py#L6) checks the normalized command name via [`cmd_name`](src/pytk/filters/base.py#L13), and the filter applies only when that name is `cargo`.

Within [`CargoFilter.filter`](src/pytk/filters/cargo.py#L10), the command’s first argument determines which helper is used. The implementation explicitly branches on the following subcommands:

| Cargo subcommand | Helper method | Notes |
|---|---|---|
| `build` | [`_filter_build`](src/pytk/filters/cargo.py#L25) | Compresses build progress and preserves error-oriented lines |
| `test` | [`_filter_test`](src/pytk/filters/cargo.py#L79) | Removes passing test noise |
| `clippy` | [`_filter_clippy`](src/pytk/filters/cargo.py#L88) | Removes “checking” noise while keeping non-noise output |
| `add` / `update` | [`_filter_add_update`](src/pytk/filters/cargo.py#L99) | Compressed dependency changes are summarized |
| `run` | [`_filter_run`](src/pytk/filters/cargo.py#L131) | Removes build lines from cargo-run style output |

If the command is `cargo` but the subcommand is not one of these values, the implementation falls through and returns the cleaned output unchanged. The filter also strips ANSI sequences before any subcommand-specific logic runs, via [`strip_ansi`](src/pytk/filters/base.py#L8).

> **Sources:** `src/pytk/filters/cargo.py` · L6–L23 · [`CargoFilter.matches`](src/pytk/filters/cargo.py#L6) · [`CargoFilter.filter`](src/pytk/filters/cargo.py#L10) · [`CargoFilter._filter_build`](src/pytk/filters/cargo.py#L25) · [`CargoFilter._filter_test`](src/pytk/filters/cargo.py#L79) · [`CargoFilter._filter_clippy`](src/pytk/filters/cargo.py#L88) · [`CargoFilter._filter_add_update`](src/pytk/filters/cargo.py#L99) · [`CargoFilter._filter_run`](src/pytk/filters/cargo.py#L131)

## Compression behavior by subcommand

### `cargo build`

[`CargoFilter._filter_build`](src/pytk/filters/cargo.py#L25) is the most involved helper. It processes the build output line-by-line and uses regular-expression matching to suppress noisy progress lines while preserving lines that matter for debugging. The implementation also consults the shared cache helpers [`get`](src/pytk/cache.py#L15) and [`set`](src/pytk/cache.py#L25), indicating that some build output can be remembered and reused rather than reprocessed every time.

From the visible logic, the key behaviors are:

- suppress selected progress lines;
- preserve error-related lines;
- retain final image or summary-style lines when they are detected;
- collapse the stream into a shorter list of retained lines.

The helper’s control flow is optimized for “keep the signal, drop the build chatter.” It is not a generic pretty-printer; it only implements the transformations evidenced in the function body and the tests.

### `cargo test`

[`CargoFilter._filter_test`](src/pytk/filters/cargo.py#L79) is short and focused. It scans each line and removes passing-test noise, then rejoins the remaining lines. The helper is intentionally conservative: it does not attempt to reformat test output broadly, only to remove lines that match the expected passing patterns.

### `cargo clippy`

[`CargoFilter._filter_clippy`](src/pytk/filters/cargo.py#L88) follows the same pattern as the test helper, but its matching targets `clippy` output instead. The implementation strips lines associated with routine “checking” progress while leaving other content intact. The net effect is a smaller result that still preserves the interesting output.

### `cargo add` and `cargo update`

[`CargoFilter._filter_add_update`](src/pytk/filters/cargo.py#L99) handles dependency-management commands. The implementation groups and compresses output rather than preserving every raw line. It is the only helper in this file that visibly introduces summary-style output for add/update flows, and it appears designed to condense verbose dependency resolution into a small number of meaningful lines.

The observable behavior is:

- related lines are grouped;
- repeated or low-value noise is dropped;
- short summary output is produced instead of a full transcript.

### `cargo run`

[`CargoFilter._filter_run`](src/pytk/filters/cargo.py#L131) filters run output by removing build-related lines. This makes sense in the context of the rest of the file: the goal is not to suppress the program’s own output, but to discard the Cargo scaffolding around it.

> **Sources:** `src/pytk/filters/cargo.py` · L25–L138 · [`CargoFilter._filter_build`](src/pytk/filters/cargo.py#L25) · [`CargoFilter._filter_test`](src/pytk/filters/cargo.py#L79) · [`CargoFilter._filter_clippy`](src/pytk/filters/cargo.py#L88) · [`CargoFilter._filter_add_update`](src/pytk/filters/cargo.py#L99) · [`CargoFilter._filter_run`](src/pytk/filters/cargo.py#L131) · `src/pytk/cache.py` · L15–L25 · [`get`](src/pytk/cache.py#L15) · [`set`](src/pytk/cache.py#L25)

## Helper-method reference

| Helper | Signature | Purpose | Observable output shape |
|---|---|---|---|
| [`CargoFilter._filter_build`](src/pytk/filters/cargo.py#L25) | `_filter_build(self, output, cfg)` | Compress `cargo build` output | Keeps selected non-noise lines, especially errors and key end-state lines |
| [`CargoFilter._filter_test`](src/pytk/filters/cargo.py#L79) | `_filter_test(self, output)` | Compress `cargo test` output | Removes passing-test chatter and returns a shorter transcript |
| [`CargoFilter._filter_clippy`](src/pytk/filters/cargo.py#L88) | `_filter_clippy(self, output)` | Compress `cargo clippy` output | Drops routine checking/progress lines |
| [`CargoFilter._filter_add_update`](src/pytk/filters/cargo.py#L99) | `_filter_add_update(self, output)` | Compress `cargo add` / `cargo update` output | Groups lines into a compact dependency summary |
| [`CargoFilter._filter_run`](src/pytk/filters/cargo.py#L131) | `_filter_run(self, output)` | Compress `cargo run` output | Removes build lines and preserves the program-relevant output |

This table intentionally stays close to the implementation. It does not infer extra behavior beyond the line transforms visible in the helper bodies and the surrounding dispatch in [`CargoFilter.filter`](src/pytk/filters/cargo.py#L10).

> **Sources:** `src/pytk/filters/cargo.py` · L10–L145 · [`CargoFilter.filter`](src/pytk/filters/cargo.py#L10) · [`CargoFilter._filter_build`](src/pytk/filters/cargo.py#L25) · [`CargoFilter._filter_test`](src/pytk/filters/cargo.py#L79) · [`CargoFilter._filter_clippy`](src/pytk/filters/cargo.py#L88) · [`CargoFilter._filter_add_update`](src/pytk/filters/cargo.py#L99) · [`CargoFilter._filter_run`](src/pytk/filters/cargo.py#L131)

## Before/after example

The `cargo run` path is the clearest example of the filter’s intent: preserve the meaningful program output while removing Cargo’s build scaffolding. A representative before/after shape looks like this:

| Before | After |
|---|---|
| ```text
   Compiling mycrate v0.1.0
   Finished dev [unoptimized + debuginfo] target(s) in 1.23s
   Running `target/debug/mycrate`
   server started on 127.0.0.1:8080
   ``` | ```text
   Running `target/debug/mycrate`
   server started on 127.0.0.1:8080
   ``` |

This mirrors the behavior of [`CargoFilter._filter_run`](src/pytk/filters/cargo.py#L131), which removes build-related lines and leaves the command’s useful output intact. The same “reduce noise, keep signal” philosophy is visible across the other helpers as well.

> **Sources:** `src/pytk/filters/cargo.py` · L131–L138 · [`CargoFilter._filter_run`](src/pytk/filters/cargo.py#L131)

## Savings example

[`CargoFilter.savings_example`](src/pytk/filters/cargo.py#L140) exists to provide a compact representative savings sample for UI/reporting paths such as `pytk list-filters`. The analysis data shows the method is present, but not its internal literal values. So the only safe statement is that it returns a savings example in the same shape used by [`BaseFilter.savings_example`](src/pytk/filters/base.py#L33): a before/after pair plus a short description.

That means the Cargo filter participates in the repository’s standard filter-discovery experience, but the actual numeric savings in the example are determined by the implementation in the source file rather than by any additional documented contract here.

> **Sources:** `src/pytk/filters/cargo.py` · L140–L145 · [`CargoFilter.savings_example`](src/pytk/filters/cargo.py#L140) · `src/pytk/filters/base.py` · L33–L35 · [`BaseFilter.savings_example`](src/pytk/filters/base.py#L33)

## Notes on implementation scope

This page intentionally avoids projecting broader Rust toolchain semantics onto the code. The implementation evidence here is limited to:

- command-name matching through [`cmd_name`](src/pytk/filters/base.py#L13);
- ANSI stripping through [`strip_ansi`](src/pytk/filters/base.py#L8);
- subcommand dispatch inside [`CargoFilter.filter`](src/pytk/filters/cargo.py#L10);
- helper-specific line compression in the five private methods;
- savings-example support through [`CargoFilter.savings_example`](src/pytk/filters/cargo.py#L140).

Anything beyond that would require reading the full source body directly or additional analysis data.

> **Sources:** `src/pytk/filters/cargo.py` · L5–L145 · [`CargoFilter`](src/pytk/filters/cargo.py#L5) · [`CargoFilter.filter`](src/pytk/filters/cargo.py#L10) · [`CargoFilter.savings_example`](src/pytk/filters/cargo.py#L140)