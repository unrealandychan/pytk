import re
from pytk.filters.base import BaseFilter, cmd_name


class GitFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        n = cmd_name(cmd)
        return bool(n) and n == "git"

    def filter(self, output: str, cmd: list[str]) -> str:
        subcmd = cmd[1] if len(cmd) > 1 else ""
        if subcmd == "status":
            return self._filter_status(output)
        elif subcmd == "diff":
            return self._filter_diff(output)
        elif subcmd == "log":
            return self._filter_log(output)
        elif subcmd in ("push", "commit", "merge"):
            return self._filter_action(output, subcmd)
        return output

    def _filter_status(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        hint_prefixes_strip = (
            "hint:",
            "nothing to commit", "nothing added",
            "On branch", "Your branch", "HEAD detached",
        )
        for line in lines:
            stripped = line.strip()
            # Strip lines that are hint-like (use "git ..." instructions)
            if re.match(r'^\s*\(use ["\']git', line):
                continue
            if any(stripped.startswith(p) or line.startswith(p) for p in hint_prefixes_strip):
                continue
            if stripped == "":
                continue
            kept.append(line)
        result = kept[:30]
        return "\n".join(result)

    def _filter_diff(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        for line in lines:
            # Strip index lines like "index abc123..def456 100644"
            if re.match(r'^index [0-9a-f]+\.\.[0-9a-f]', line):
                continue
            kept.append(line)
        result = kept[:100]
        return "\n".join(result)

    def _filter_log(self, output: str) -> str:
        lines = output.splitlines()
        entries = []
        current_hash = None
        current_msg = None
        for line in lines:
            # Full log format: "commit <hash>"
            m = re.match(r'^commit ([0-9a-f]{7,40})', line)
            if m:
                if current_hash and current_msg:
                    entries.append(f"{current_hash[:7]} {current_msg}")
                current_hash = m.group(1)
                current_msg = None
                continue
            # One-line log format: "<hash> <message>"
            m2 = re.match(r'^([0-9a-f]{7,40})\s+(.*)', line)
            if m2 and not line.startswith(" ") and not line.startswith("Author") and not line.startswith("Date"):
                entries.append(f"{m2.group(1)[:7]} {m2.group(2)}")
                continue
            # Skip Author/Date lines
            if line.startswith("Author:") or line.startswith("Date:") or line.startswith("Merge:"):
                continue
            # Commit message (indented with 4 spaces)
            if line.startswith("    ") and current_hash and current_msg is None:
                current_msg = line.strip()
        if current_hash and current_msg:
            entries.append(f"{current_hash[:7]} {current_msg}")
        return "\n".join(entries[:20])

    def _filter_action(self, output: str, subcmd: str) -> str:
        lines = [l for l in output.splitlines() if l.strip()]
        if subcmd == "push":
            # Look for "main -> origin/main" style line
            for line in lines:
                m = re.search(r'(\S+)\s+->\s+(\S+)', line)
                if m:
                    return f"ok {m.group(1)} → {m.group(2)}"
            return lines[-1] if lines else output.strip()
        elif subcmd == "commit":
            # Look for "[branch hash] message"
            for line in lines:
                m = re.match(r'\[(\S+)\s+([0-9a-f]+)\]\s+(.*)', line)
                if m:
                    return f"committed: {m.group(2)[:7]} \"{m.group(3)}\""
            return lines[-1] if lines else output.strip()
        elif subcmd == "merge":
            return lines[-1] if lines else output.strip()
        return output

    def savings_example(self) -> dict:
        return {
            "before": 4800,
            "after": 480,
            "description": "git diff with 50 changed lines — strips index lines, keeps hunks",
        }
