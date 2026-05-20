import re
from pytk.filters.base import BaseFilter

MAX_LINES = 50


class LsFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        return bool(cmd) and cmd[0] in ("ls", "find", "tree")

    def filter(self, output: str, cmd: list[str]) -> str:
        lines = output.splitlines()

        if cmd[0] == "tree":
            return self._truncate(lines)

        if cmd[0] == "find":
            return self._filter_find(lines)

        # ls
        return self._filter_ls(lines)

    def _filter_ls(self, lines: list[str]) -> str:
        cleaned = []
        for line in lines:
            # Skip total line
            if line.startswith("total "):
                continue
            # Strip permission/ownership columns from ls -la style lines
            # Pattern: permissions links owner group size date date date name
            m = re.match(
                r'^[dlcbsp\-][rwxsStT\-]{9}[\+@]?\s+\d+\s+\S+\s+\S+\s+\d+\s+\w+\s+\d+\s+[\d:]+\s+(.*)',
                line
            )
            if m:
                name = m.group(1)
                cleaned.append(name)
            else:
                cleaned.append(line)

        return self._truncate(cleaned)

    def _filter_find(self, lines: list[str]) -> str:
        # Just truncate find output
        return self._truncate(lines)

    def _truncate(self, lines: list[str]) -> str:
        if len(lines) <= MAX_LINES:
            return "\n".join(lines)
        shown = lines[:MAX_LINES]
        remaining = len(lines) - MAX_LINES
        shown.append(f"[... {remaining} more entries]")
        return "\n".join(shown)

    def savings_example(self) -> dict:
        return {
            "before": 3200,
            "after": 800,
            "description": "ls -la with 40 files — strips permissions/timestamps",
        }
