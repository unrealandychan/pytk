## v0.1.0 — 2026-05-20

### Initial Release 🎉

First public release of `pytk` — a CLI proxy that reduces LLM token consumption by 60–90% by filtering and compressing shell command outputs before they reach LLM context.

### Features

- **`pytk ls`** — strip permissions/timestamps, collapse large directories into tree format (~80% savings)
- **`pytk git`** — per-subcommand filters: `status` strips hints, `diff` strips index lines, `log` keeps hash+message only, `push`/`commit` compressed to 1 line (~75–92% savings)
- **`pytk pytest`** / `go test` / `cargo test` / `npm test` — keep failures + summary only, strip all passing lines (~90% savings)
- **`pytk grep`** / `rg` — max 50 matches, group >5 matches per file, strip binary lines (~80% savings)
- **`pytk cat`** — truncate long files to head+tail, collapse consecutive blank lines (~70% savings)
- **`pytk gain`** — show cumulative token savings stats from `~/.pytk/stats.json`
- **`pytk list-filters`** — list all registered filters with example savings
- **`pytk init`** — print integration instructions for Claude Code, Hermes, Codex
- **`pytk passthrough`** — run command without any filtering (escape hatch)

### Installation

```bash
uv tool install pytk
# or
pip install pytk
```
