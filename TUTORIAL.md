# Tutorial: Using pytk with AI Coding Agents

This tutorial shows how to integrate `pytk` into your AI coding workflow to cut token usage by 75–92%.

---

## Prerequisites

```bash
uv tool install pytk
pytk --help  # verify install
```

---

## Part 1: Understanding the Problem

Every time an AI agent runs `git status`, it gets back something like:

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update index)
  (use "git restore <file>..." to discard changes)
        modified:   src/myapp/cli.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        notes.txt
```

That's ~200 tokens. The agent only needs:

```
modified:   src/myapp/cli.py
untracked:  notes.txt
```

That's ~20 tokens. Over a 30-min session with dozens of shell calls, this adds up to **tens of thousands of wasted tokens**.

---

## Part 2: Basic Usage

Drop-in prefix — no behaviour change, just compressed output:

```bash
# Directory listing
pytk ls -la                     # strips permissions/timestamps
pytk ls -la src/                # same flags, filtered output

# Git
pytk git status                 # strips hints, keeps changed files
pytk git diff                   # strips index hash lines
pytk git diff HEAD~1 -- src/    # same flags work
pytk git log --oneline -10      # keeps hash + message only
pytk git push origin main       # compresses to: ok main → origin/main

# Tests
pytk pytest tests/              # strips passing, keeps failures + summary
pytk pytest tests/ -v -k auth   # flags passed through

# Search
pytk grep "TODO" src/ -r        # max 50 matches, grouped per file
pytk rg "def run" . --type py   # works with ripgrep too

# File reading
pytk cat src/myapp/cli.py       # truncates at 200 lines head+tail
pytk cat README.md
```

---

## Part 3: Integrating with Claude Code

### Step 1: Generate the snippet

```bash
cd your-project/
pytk init --agent claude
```

### Step 2: Add to CLAUDE.md

Create or append to `CLAUDE.md` in your project root:

```markdown
## Shell Commands — Token Efficiency
Always use `pytk <cmd>` instead of direct shell commands.

| Use this | Instead of |
|---|---|
| `pytk ls -la` | `ls -la` |
| `pytk git status` | `git status` |
| `pytk git diff` | `git diff` |
| `pytk pytest tests/` | `pytest tests/` |
| `pytk grep pattern src/` | `grep pattern src/` |
| `pytk cat file.py` | `cat file.py` |

For unfiltered output: `pytk passthrough <cmd>`
```

### Step 3: Claude now uses pytk automatically

Claude Code reads `CLAUDE.md` at the start of every session. It will prefix all matching commands with `pytk` without being asked.

---

## Part 4: Integrating with Hermes Agent

Add to your Hermes skill or system context:

```markdown
## Shell Command Efficiency
Use `pytk <cmd>` for all shell commands to reduce token consumption:
- pytk ls, pytk git status/diff/log/push, pytk pytest, pytk grep, pytk cat
- For raw output: pytk passthrough <cmd>
```

Or load the `pytk` skill if available in your Hermes setup — it instructs the agent automatically.

---

## Part 5: Integrating with Codex / OpenAI Agents

```bash
pytk init --agent codex
```

Paste the output into your `AGENTS.md`:

```markdown
## Shell Command Proxy
Prefix shell commands with `pytk` to reduce output verbosity:

  pytk ls, pytk git status, pytk pytest, pytk grep, pytk cat

Use `pytk passthrough <cmd>` for unfiltered output.
```

---

## Part 6: Tracking Your Savings

After using pytk for a while:

```bash
pytk gain
```

Example output:
```
                   pytk Token Savings
┌──────────┬──────┬─────────────┬─────────────┬───────────┐
│ Command  │ Runs │ Orig tokens │ Filt tokens │ Reduction │
├──────────┼──────┼─────────────┼─────────────┼───────────┤
│ git      │   24 │      28,800 │       2,880 │       90% │
│ pytest   │   10 │      80,000 │       6,000 │       92% │
│ ls       │   15 │      12,000 │       3,000 │       75% │
│ grep     │   12 │      15,000 │       2,700 │       82% │
│ cat      │    8 │      24,000 │       4,800 │       80% │
│ TOTAL    │   69 │     159,800 │      19,380 │       88% │
└──────────┴──────┴─────────────┴─────────────┴───────────┘
```

Stats stored in `~/.pytk/stats.json` — safe to delete anytime.

---

## Part 7: Edge Cases & Escape Hatch

### When to use passthrough

```bash
# Need full git log graph
pytk passthrough git log --oneline --graph --all

# Need exact pytest output for debugging
pytk passthrough pytest tests/test_specific.py -s

# Command not supported by pytk (passes through anyway, but explicit is clearer)
pytk passthrough docker compose up
```

### Commands pytk doesn't filter

Anything not in the supported list passes through **unchanged** — so it's always safe to prefix with `pytk`. Example:

```bash
pytk docker build .     # no filter → raw output (same as running docker build .)
pytk make install       # no filter → raw output
```

---

## Summary

| Step | Action |
|---|---|
| Install | `uv tool install pytk` |
| Use | Prefix commands: `pytk git status`, `pytk pytest`, etc. |
| Integrate | Add snippet to `CLAUDE.md` / `AGENTS.md` via `pytk init` |
| Track | `pytk gain` to see cumulative savings |
| Escape | `pytk passthrough <cmd>` for raw output |
