---
slug: module-git-filter
title: "Git Filter Implementation"
section: core-components
tags: [modules, reference]
pin: false
importance: 80
created_at: 2026-05-23T04:41:32Z
rekipedia_version: 0.17.15
---

# Git Filter Implementation

## Overview

The Git-specific output reducer is implemented by [`GitFilter`](src/pytk/filters/git.py#L5) in [`src/pytk/filters/git.py`](src/pytk/filters/git.py). It is a focused `BaseFilter` subclass that recognizes Git commands via [`GitFilter.matches`](src/pytk/filters/git.py#L6), then routes the raw command output through [`GitFilter.filter`](src/pytk/filters/git.py#L10). The implementation is intentionally command-family oriented: it has dedicated handlers for status-like, diff-like, log-like, and action-like Git subcommands, each of which trims high-volume or repetitive details while preserving the information humans usually need to make the next decision.

At a high level, the filter performs three kinds of transformations:

1. **Normalization** — ANSI escapes are removed before parsing so formatting does not interfere with matching or line handling.
2. **Compression** — repetitive metadata and boilerplate are dropped or collapsed into shorter summaries.
3. **Message shortening** — commit messages are stripped of ref decorations and truncated when they are long.

The result is a concise textual summary that remains recognizably “Git output” but is far cheaper to send downstream.

> **Sources:** `src/pytk/filters/git.py` · L5–L124 · [`GitFilter`](src/pytk/filters/git.py#L5), [`GitFilter.matches`](src/pytk/filters/git.py#L6), [`GitFilter.filter`](src/pytk/filters/git.py#L10)

## Supported Git command families

[`GitFilter.matches`](src/pytk/filters/git.py#L6) determines whether a command should be handled by checking the executable name from the command vector. The filter is designed around the following Git families, as reflected by the internal helper methods it dispatches to:

| Git family / subcommands | Helper method | What it preserves |
|---|---|---|
| Status-like commands | [`GitFilter._filter_status`](src/pytk/filters/git.py#L23) | Changed/untracked file lines, while dropping hints and other noise |
| Diff-like commands | [`GitFilter._filter_diff`](src/pytk/filters/git.py#L46) | Diff headers and hunk/file content, while removing index lines |
| Log-like commands | [`GitFilter._filter_log`](src/pytk/filters/git.py#L70) | Commit entries, but with compressed commit messages |
| Action-like commands | [`GitFilter._filter_action`](src/pytk/filters/git.py#L99) | Short outcome summary for push/commit-like operations |

`[GitFilter.filter`](src/pytk/filters/git.py#L10)` uses the subcommand in `cmd[1]` to select the appropriate specialization. The routing is shallow and direct, which keeps the behavior predictable: the first token determines that the filter applies, and the second token determines how aggressively the output is reduced.

### Routing model

```mermaid
flowchart TD
  A[command cmd] --> B[GitFilter.matches]
  B --> C[GitFilter.filter]
  C --> D{cmd[1]}
  D -->|status| E[GitFilter._filter_status]
  D -->|diff| F[GitFilter._filter_diff]
  D -->|log| G[GitFilter._filter_log]
  D -->|push / commit / other actions| H[GitFilter._filter_action]
  E --> I[shortened output]
  F --> I
  G --> I
  H --> I
```

This structure is reflected directly in [`GitFilter.filter`](src/pytk/filters/git.py#L10), which dispatches to the relevant helper based on the command’s subcommand token.

> **Sources:** `src/pytk/filters/git.py` · L6–L21 · [`GitFilter.matches`](src/pytk/filters/git.py#L6), [`GitFilter.filter`](src/pytk/filters/git.py#L10), [`GitFilter._filter_status`](src/pytk/filters/git.py#L23), [`GitFilter._filter_diff`](src/pytk/filters/git.py#L46), [`GitFilter._filter_log`](src/pytk/filters/git.py#L70), [`GitFilter._filter_action`](src/pytk/filters/git.py#L99)

## Normalization and compression rules

Before any Git-specific parsing occurs, [`GitFilter.filter`](src/pytk/filters/git.py#L10) strips ANSI escape sequences using the shared [`strip_ansi`](src/pytk/filters/base.py#L8) helper. This is important because Git output can include colored hints or terminal formatting; the filter needs plain text to make reliable line-level decisions.

Once normalized, the helper methods apply command-specific compression rules:

### Status output normalization

[`GitFilter._filter_status`](src/pytk/filters/git.py#L23) scans the status output line by line and keeps the useful file-state information. The observable behavior is:

- preserve file change lines;
- drop hint paragraphs and other explanatory noise;
- avoid expanding the status output into full prose.

This is a classic “keep the delta, discard the tutorial” strategy: the file names and status markers are retained, but the verbose advisory text Git often prints is removed.

### Diff output normalization

[`GitFilter._filter_diff`](src/pytk/filters/git.py#L46) is narrower and more conservative. It strips the `index ...` lines that usually carry commit-sha metadata, while leaving the surrounding diff structure intact. That means readers still see which files changed and what the patch looks like, but the redundant index bookkeeping is gone.

### Log message compression

The key shortening primitive is [`GitFilter._compress_msg`](src/pytk/filters/git.py#L62). Its docstring states that it **strips ref decorations and truncates long commit messages**. In practice, this means commit subjects are normalized by removing decorative references like branch/tag adornments, then shortened when they exceed the intended display budget.

This is especially valuable in log output, where the same commit may be referenced by multiple decorated forms and where subjects can be much longer than a compact summary needs.

### Action output compression

[`GitFilter._filter_action`](src/pytk/filters/git.py#L99) handles operation-result output from Git actions such as push or commit-like flows. It reduces multi-line status text into a short, human-readable result line or two, rather than preserving the full verbose transcript of the command.

> **Sources:** `src/pytk/filters/git.py` · L23–L117 · [`GitFilter._filter_status`](src/pytk/filters/git.py#L23), [`GitFilter._filter_diff`](src/pytk/filters/git.py#L46), [`GitFilter._compress_msg`](src/pytk/filters/git.py#L62), [`GitFilter._filter_log`](src/pytk/filters/git.py#L70), [`GitFilter._filter_action`](src/pytk/filters/git.py#L99); `src/pytk/filters/base.py` · L8–L10 · [`strip_ansi`](src/pytk/filters/base.py#L8)

## Helper-to-subcommand mapping

The implementation is easiest to understand as a dispatch table from helper method to Git subcommand family:

| Helper method | Git subcommands handled | Role |
|---|---|---|
| [`GitFilter._filter_status`](src/pytk/filters/git.py#L23) | `status` | Remove hints and keep changed-file information |
| [`GitFilter._filter_diff`](src/pytk/filters/git.py#L46) | `diff` | Remove `index` metadata while preserving diff structure |
| [`GitFilter._compress_msg`](src/pytk/filters/git.py#L62) | Used by `log` | Shorten a commit message after removing ref decorations |
| [`GitFilter._filter_log`](src/pytk/filters/git.py#L70) | `log` | Keep commits, but compress each commit subject |
| [`GitFilter._filter_action`](src/pytk/filters/git.py#L99) | action-style subcommands such as push/commit flows | Collapse verbose success/failure text into a shorter result |

This table captures the implemented behavior without assuming unsupported subcommands beyond what the filter clearly handles via its internal routing.

> **Sources:** `src/pytk/filters/git.py` · L23–L124 · [`GitFilter._filter_status`](src/pytk/filters/git.py#L23), [`GitFilter._filter_diff`](src/pytk/filters/git.py#L46), [`GitFilter._compress_msg`](src/pytk/filters/git.py#L62), [`GitFilter._filter_log`](src/pytk/filters/git.py#L70), [`GitFilter._filter_action`](src/pytk/filters/git.py#L99), [`GitFilter.savings_example`](src/pytk/filters/git.py#L119)

## Message-shortening behavior

The most explicit shortening behavior appears in [`GitFilter._compress_msg`](src/pytk/filters/git.py#L62). The helper’s documented purpose is to remove ref decorations and truncate long commit messages, which matters because Git log output often includes:

- branch or tag decorations;
- commit subjects that are longer than a concise model context budget;
- repetitive boilerplate that adds little semantic value.

[`GitFilter._filter_log`](src/pytk/filters/git.py#L70) uses this helper to rewrite log entries into a more compact form. The overall effect is that commit listings remain readable and traceable, but each message occupies fewer tokens. This is a better fit for downstream summarization than raw `git log` text, especially for repositories with long commit subjects or heavily decorated refs.

Although the analysis data does not expose the literal formatting strings, it does show clearly that log entries are parsed line-by-line and passed through message compression. That makes the behavior straightforward to reason about: log detail is preserved where it identifies the commit, while subject text is shortened where it would otherwise dominate the output.

> **Sources:** `src/pytk/filters/git.py` · L62–L97 · [`GitFilter._compress_msg`](src/pytk/filters/git.py#L62), [`GitFilter._filter_log`](src/pytk/filters/git.py#L70)

## Example transformation

The filter’s tests demonstrate the intended effect: verbose Git output becomes shorter and more focused. A representative transformation pattern is:

| Input family | Typical noisy content | Transformed output |
|---|---|---|
| `git status` | Hints and explanatory text | Only changed/untracked file lines remain |
| `git diff` | `index ...` metadata lines | Diff body remains, index metadata removed |
| `git log` | Decorated refs and long commit subjects | Messages are stripped of decorations and shortened |
| action output | Multi-line success transcript | Short outcome summary |

A concise example of the style of transformation is:

```text
Before:  On branch main
         Your branch is up to date with 'origin/main'.
         modified: src/app.py

After:   modified: src/app.py
```

Similarly, log output is compressed by removing decorations and truncating long subjects:

```text
Before:  commit abc123 (HEAD -> main, origin/main)
         Author: Someone
         Date:   ...

         Fix the very long commit message that goes on and on...

After:   commit abc123
         Fix the very long commit message...
```

These examples align with the helper structure in [`GitFilter._filter_status`](src/pytk/filters/git.py#L23), [`GitFilter._filter_diff`](src/pytk/filters/git.py#L46), [`GitFilter._filter_log`](src/pytk/filters/git.py#L70), and [`GitFilter._filter_action`](src/pytk/filters/git.py#L99), though the exact literal output depends on the command and the raw text being filtered.

> **Sources:** `src/pytk/filters/git.py` · L23–L124 · [`GitFilter._filter_status`](src/pytk/filters/git.py#L23), [`GitFilter._filter_diff`](src/pytk/filters/git.py#L46), [`GitFilter._filter_log`](src/pytk/filters/git.py#L70), [`GitFilter._filter_action`](src/pytk/filters/git.py#L99), [`GitFilter.savings_example`](src/pytk/filters/git.py#L119)

## Savings example

[`GitFilter.savings_example`](src/pytk/filters/git.py#L119) provides the example summary used by the filter registry and filter listing UI. The analysis data confirms that the method exists and is part of the filter’s public “what does this save?” contract, but it does not expose the exact numeric values or description text. What is observable is that GitFilter participates in the same savings-example convention as other filters, allowing the system to present a before/after estimate for Git output reduction.

This is useful because Git commands are often high-chatter but low-entropy in their raw form: the savings example communicates that the filter is not merely cosmetically changing output, but meaningfully reducing token volume.

> **Sources:** `src/pytk/filters/git.py` · L119–L124 · [`GitFilter.savings_example`](src/pytk/filters/git.py#L119)