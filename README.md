# pytk — Python Token Killer

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![MIT License](https://img.shields.io/badge/license-MIT-green)
![PyPI](https://img.shields.io/pypi/v/pytk)

> **CLI proxy that reduces LLM token consumption by ~50%** by filtering and compressing shell command outputs before they reach AI context.

When AI coding agents (Claude Code, Codex, Cursor, Hermes, etc.) run shell commands, the raw verbose output wastes thousands of tokens per session. `pytk` sits transparently between the agent and the shell — stripping noise, keeping only what matters.

---

## Token Savings — Real Benchmark

> Measured on pytk's own codebase using [`tiktoken`](https://github.com/openai/tiktoken) (cl100k\_base encoding), 3 runs per command.
> Run it yourself: `python scripts/benchmark.py`

| Operation | Raw tokens | With pytk | Savings |
|---|---:|---:|:---:|
| `git status` | 74 | 7 | **-90%** |
| `git diff HEAD~1` | 118 | 103 | **-12%** |
| `git log --oneline -20` | 341 | 341 | **-0%** |
| `ls -la` | 339 | 41 | **-87%** |
| `find *.py` | 391 | 391 | **-0%** |
| `grep 'def '` | 2,892 | 1,384 | **-52%** |
| `cat cli.py` | 6,127 | 1,049 | **-82%** |
| `pytest -v` | 4,015 | 153 | **-96%** |
| **Total** | **19,939** | **4,765** | **-76%** |

> Commands with 0% savings (git log, find) have filters that preserve structure by design — future versions will add smarter compression for these.

---

## Installation

```bash
# Recommended — installs as isolated global tool
uv tool install pytk

# Or with pip
pip install pytk

# Verify
pytk --help
```

---

## Quick Start

`pytk` is a **drop-in prefix** — just add `pytk` before any supported command:

```bash
pytk ls -la src/
pytk git status
pytk git diff HEAD~1
pytk pytest tests/ -v
pytk grep "def run" src/ -r
pytk cat README.md
```

That's it. Same flags, same arguments — just compressed output.

---

## Tutorial

### 1. See the difference

Let's compare raw vs filtered output side by side.

**Raw `git status`** (~800 tokens):
```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update index)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   src/pytk/cli.py
        modified:   src/pytk/filters/git.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        tests/test_new.py

no changes added to commit (use "git add" and/or "git commit -a")
```

**`pytk git status`** (~80 tokens):
```
modified:   src/pytk/cli.py
modified:   src/pytk/filters/git.py
untracked:  tests/test_new.py
```

---

### 2. Test output compression

**Raw `pytest`** (200+ lines, ~4,000 tokens):
```
collected 49 items

tests/test_cli.py::test_gain_no_stats PASSED                           [  2%]
tests/test_cli.py::test_list_filters PASSED                            [  4%]
tests/test_filters_git.py::test_git_status_strips_hints PASSED         [  6%]
... (46 more passing lines)
tests/test_filters_git.py::test_git_push_compressed FAILED             [ 95%]

FAILURES
=========
...long traceback...
```

**`pytk pytest tests/`** (~15 lines, ~300 tokens):
```
FAILED: tests/test_filters_git.py::test_git_push_compressed
AssertionError: expected 'ok main' got 'ok main → origin/main'

1 failed, 48 passed in 0.14s
```

---

### 3. Track your savings

Every filtered command appends stats to `~/.pytk/stats.json`. View cumulative savings:

```bash
pytk gain
```

Output:
```
                   pytk Token Savings
┌──────────┬──────┬─────────────┬─────────────┬───────────┐
│ Command  │ Runs │ Orig tokens │ Filt tokens │ Reduction │
├──────────┼──────┼─────────────┼─────────────┼───────────┤
│ git      │   12 │      14,400 │       1,440 │       90% │
│ pytest   │    5 │      40,000 │       3,000 │       92% │
│ ls       │    8 │       6,400 │       1,600 │       75% │
│ grep     │    6 │       7,500 │       1,350 │       82% │
│ cat      │    4 │      12,000 │       2,400 │       80% │
│ TOTAL    │   35 │      80,300 │       9,790 │       88% │
└──────────┴──────┴─────────────┴─────────────┴───────────┘
```

---

### 4. Escape hatch

Output looks wrong? Use `passthrough` to get raw unfiltered output:

```bash
pytk passthrough git log --oneline --graph
```

---

### 5. See all filters

```bash
pytk list-filters
```

---

## AI Agent Integration

### Claude Code

Run this in your project root:

```bash
pytk init --agent claude
```

Then paste the output into your `CLAUDE.md`. Claude will automatically prefix commands with `pytk`.

Or add manually to `CLAUDE.md`:

```markdown
## Shell Commands
Always use `pytk <cmd>` instead of running shell commands directly.
This reduces token usage by filtering verbose output.

Examples:
  pytk ls -la src/
  pytk git status
  pytk git diff HEAD~1
  pytk pytest tests/
  pytk grep 'pattern' src/ -r
  pytk cat file.py
```

### Hermes Agent

```bash
pytk init --agent hermes
```

Or add to your Hermes system prompt / skill:

```python
# Use pytk for all shell commands to reduce token usage
# pytk ls, pytk git, pytk pytest, pytk grep, pytk cat
```

### Codex / OpenAI Agents

```bash
pytk init --agent codex
```

Adds a section to `AGENTS.md` instructing Codex to use `pytk` for shell commands.

### Any agent (generic)

The key principle: instruct your agent to **prefix shell commands with `pytk`**. The agent doesn't need to know anything about pytk internals — it just uses it like a regular command.

```markdown
## Token Efficiency
Prefix all shell commands with `pytk` to reduce output verbosity:
pytk ls, pytk git status, pytk pytest, pytk grep, pytk cat
```

---

## Supported Commands

| Command | Filter | What's removed | Savings |
|---|---|---|---|
| `ls`, `find`, `tree` | LsFilter | permissions, uid, gid, size, timestamps | ~75% |
| `git status` | GitFilter | hints, tracking info, usage instructions | ~80% |
| `git diff` | GitFilter | `index xxxx..yyyy` lines, keeps hunks | ~90% |
| `git log` | GitFilter | author, date — keeps hash + message only | ~80% |
| `git push/commit/merge` | GitFilter | progress lines, compressed to 1 line | ~92% |
| `pytest`, `python -m pytest` | TestFilter | passing test lines, progress bars | ~92% |
| `go test`, `cargo test`, `npm test` | TestFilter | passing test lines, progress bars | ~92% |
| `grep`, `rg`, `ag` | GrepFilter | binary matches, excess per-file results | ~82% |
| `cat`, `head`, `tail` | CatFilter | middle of long files, excess blank lines | ~80% |

Commands not in the list pass through unmodified — always safe to prefix with `pytk`.

---

## CLI Reference

```bash
pytk <command> [args...]        # Run command with filter applied
pytk gain                       # Show cumulative token savings
pytk init [--agent NAME]        # Print agent integration snippet
pytk passthrough <cmd> [args]   # Run without filtering
pytk list-filters               # Show all filters + example savings
```

`--agent` options: `claude`, `hermes`, `codex` (default: prints all)

---

## Contributing

```bash
git clone https://github.com/unrealandychan/pytk
cd pytk
uv sync --extra dev
pytest tests/ -v
```

### Adding a new filter

1. Create `src/pytk/filters/myfilter.py` extending `BaseFilter`:

```python
from pytk.filters.base import BaseFilter

class DockerFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        return bool(cmd) and cmd[0] == "docker"

    def filter(self, output: str, cmd: list[str]) -> str:
        # your compression logic
        return output

    def savings_example(self) -> dict:
        return {"before": 500, "after": 100, "description": "docker ps with 10 containers"}
```

2. Register in `src/pytk/filters/registry.py`:

```python
from pytk.filters.myfilter import DockerFilter
FILTERS = [..., DockerFilter()]
```

3. Add tests in `tests/test_filters_myfilter.py`
4. Open a PR 🎉

---

## Roadmap

### ✅ Done (v0.2.0)
- [x] `docker ps / logs / build / compose` filter
- [x] `kubectl get / describe / logs / rollout` filter
- [x] `npm / yarn / pnpm / npx` filter
- [x] `curl` / `wget` response filter
- [x] Shell hook mode (`pytk hook enable` — auto-intercept without `pytk` prefix)
- [x] VS Code extension scaffold
- [x] Claude Code / Cursor / Windsurf / Gemini PreToolUse hooks
- [x] Output caching, `--dry-run`, `pytk doctor`

### 🔜 Next
- [ ] **ANSI color stripping** — filters fail silently when output has color codes (`git diff --color`, `pytest --color=yes`)
- [ ] **`uv run <cmd>` dispatch** — `uv run pytest` should route to TestFilter, not PackageManagerFilter
- [ ] **Linting filters** — `ruff check`, `mypy`, `flake8`, `tsc --noEmit` (strip passing files, keep errors)
- [ ] **`python3` shell hook** — `python3 -m pytest` not intercepted by shell hook (`python3` missing from SUPPORTED_CMDS)
- [ ] **Graceful filter fallback** — if a filter crashes, return raw output instead of propagating exception
- [ ] **`git diff` / `git status` truncation notice** — add `[... N more lines]` when output is capped
- [ ] **`global.enabled` / `passthrough_on_error` config** — these keys exist but are not yet wired up
- [ ] **`cargo run` subcommand** support
- [ ] **`poetry install` / `poetry run`** support
- [ ] **`docker inspect`** JSON compression
- [ ] **VS Code extension** publish to Marketplace

---

## License

MIT — © 2026 unrealandychan
