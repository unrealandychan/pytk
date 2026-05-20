# pytk

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![MIT License](https://img.shields.io/badge/license-MIT-green)
![PyPI](https://img.shields.io/pypi/v/pytk)

> **CLI proxy that reduces LLM token consumption by filtering and compressing shell command outputs.**

When AI coding agents run shell commands, the verbose output wastes thousands of tokens. `pytk` sits between the agent and the shell, stripping noise and keeping only what matters.

---

## Token Savings

| Command | Typical Input | Filtered Output | Reduction |
|---------|--------------|-----------------|-----------|
| `ls -la` (40 files) | ~800 tokens | ~200 tokens | **75%** |
| `git diff` (50 lines changed) | ~1200 tokens | ~120 tokens | **90%** |
| `pytest` (100 passing, 2 failing) | ~2000 tokens | ~150 tokens | **92%** |
| `grep` (60 matches) | ~1250 tokens | ~225 tokens | **82%** |
| `cat` (300-line file) | ~3000 tokens | ~600 tokens | **80%** |

---

## Installation

```bash
# Recommended (isolated tool)
uv tool install pytk

# Or with pip
pip install pytk
```

---

## Quick Start

```bash
# Instead of: ls -la src/
pytk ls -la src/

# Instead of: git status
pytk git status

# Instead of: git diff HEAD~1
pytk git diff HEAD~1

# Instead of: pytest tests/
pytk pytest tests/

# Instead of: grep "def run" src/ -r
pytk grep "def run" src/ -r

# Instead of: cat README.md
pytk cat README.md
```

---

## Supported Commands

| Command | Filter | What's removed |
|---------|--------|----------------|
| `ls`, `find`, `tree` | LsFilter | permissions, uid, gid, size, timestamps |
| `git status` | GitFilter | hints, branch tracking verbose text |
| `git diff` | GitFilter | index hash lines, keeps hunks |
| `git log` | GitFilter | author, date — keeps hash + message |
| `git push/commit` | GitFilter | compresses to 1-line summary |
| `pytest`, `go test`, etc. | TestFilter | passing tests, progress bars |
| `grep`, `rg`, `ag` | GrepFilter | binary matches, excess per-file matches |
| `cat`, `head`, `tail` | CatFilter | middle of long files, excess blank lines |

---

## CLI Commands

```bash
pytk <command> [args...]   # Run with filter applied
pytk gain                  # Show token savings stats
pytk init [--agent NAME]   # Print agent integration instructions
pytk passthrough <cmd>     # Run without filtering (escape hatch)
pytk list-filters          # Show all filters + example savings
```

---

## `pytk gain` Output Example

```
                pytk Token Savings
┌──────────┬──────┬─────────────┬─────────────┬───────┬───────────┐
│ Command  │ Runs │ Orig tokens │ Filt tokens │ Saved │ Reduction │
├──────────┼──────┼─────────────┼─────────────┼───────┼───────────┤
│ git      │   12 │       14400 │        1440 │ 12960 │       90% │
│ pytest   │    5 │       40000 │        3000 │ 37000 │       92% │
│ ls       │    8 │        6400 │        1600 │  4800 │       75% │
│ TOTAL    │   25 │       60800 │        6040 │ 54760 │       90% │
└──────────┴──────┴─────────────┴─────────────┴───────┴───────────┘
```

---

## Agent Integration

### Claude Code

```bash
pytk init --agent claude
```

Adds to `CLAUDE.md`:
```markdown
## Shell Commands
Use `pytk <cmd>` instead of running shell commands directly.
```

### Hermes Agent

```bash
pytk init --agent hermes
```

### Codex

```bash
pytk init --agent codex
```

Adds to `AGENTS.md`:
```markdown
## Shell Command Proxy
Prefix shell commands with `pytk` to reduce output verbosity.
```

---

## Contributing

```bash
git clone https://github.com/youruser/pytk
cd pytk
uv sync --extra dev
pytest tests/ -v
```

PRs welcome! To add a new filter:
1. Create `src/pytk/filters/myfilter.py` extending `BaseFilter`
2. Add it to `FILTERS` in `registry.py`
3. Add tests in `tests/test_filters_myfilter.py`

---

## License

MIT
