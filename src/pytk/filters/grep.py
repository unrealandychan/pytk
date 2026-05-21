import re
from collections import defaultdict
from pytk.filters.base import BaseFilter, cmd_name, strip_ansi

MAX_MATCHES = 50
MAX_PER_FILE = 5
SHOW_PER_FILE = 3


class GrepFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        n = cmd_name(cmd)
        return bool(n) and n in ("grep", "rg", "ripgrep", "ag")

    def filter(self, output: str, cmd: list[str]) -> str:
        output = strip_ansi(output)
        from pytk.config import load_config, get_filter_config
        cfg = get_filter_config(load_config(), "grep")
        max_matches = cfg.get("max_results", MAX_MATCHES)

        lines = output.splitlines()
        # Strip binary match lines
        lines = [l for l in lines if not re.search(r'Binary file .* matches', l)]

        # Group by filename (pattern: filename:linenum:content or filename:content)
        file_matches: dict[str, list[str]] = defaultdict(list)
        unkeyed: list[str] = []

        for line in lines:
            # Try to detect file:lineno:content or file:content
            m = re.match(r'^([^:\n]+):(\d+):(.*)', line)
            if m:
                file_matches[m.group(1)].append(line)
            else:
                m2 = re.match(r'^([^:\n]+):(.*)', line)
                if m2:
                    file_matches[m2.group(1)].append(line)
                else:
                    unkeyed.append(line)

        result = []
        total = 0

        for fname, flines in file_matches.items():
            if total >= max_matches:
                break
            if len(flines) > MAX_PER_FILE:
                shown = flines[:SHOW_PER_FILE]
                extra = len(flines) - SHOW_PER_FILE
                result.extend(shown)
                result.append(f"[+{extra} more in {fname}]")
                total += SHOW_PER_FILE
            else:
                result.extend(flines)
                total += len(flines)

        for line in unkeyed:
            if total >= max_matches:
                break
            result.append(line)
            total += 1

        if total >= max_matches and len(lines) > max_matches:
            skipped = len(lines) - MAX_MATCHES
            result.append(f"[... {skipped} more matches truncated]")

        return "\n".join(result)

    def savings_example(self) -> dict:
        return {
            "before": 5000,
            "after": 900,
            "description": "grep with 60 matches across 5 files — truncated + grouped",
        }
