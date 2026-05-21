import re
from pytk.filters.base import BaseFilter, cmd_name, strip_ansi


class UvFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        return bool(cmd) and cmd_name(cmd) == "uv"

    def filter(self, output: str, cmd: list[str]) -> str:
        # For `uv run <cmd>`, dispatch to the inner command's filter
        if len(cmd) >= 3 and cmd[1] == "run":
            inner = cmd[2:]
            # handle `uv run python -m pytest` -> inner is ['python', '-m', 'pytest', ...]
            from pytk.filters.registry import get_filter
            inner_filter = get_filter(inner)
            if inner_filter is not None and not isinstance(inner_filter, UvFilter):
                return inner_filter.filter(output, inner)
            # Also handle `uv run python -m pytest` where inner[0]=='python'
            if inner and inner[0] == "python":
                # find -m <module>
                if "-m" in inner:
                    idx = inner.index("-m")
                    if idx + 1 < len(inner):
                        module_cmd = [inner[idx + 1]] + inner[idx + 2:]
                        module_filter = get_filter(module_cmd)
                        if module_filter is not None and not isinstance(module_filter, UvFilter):
                            return module_filter.filter(output, module_cmd)

        # Default: package-manager style filtering (strip uv noise)
        output = strip_ansi(output)
        lines = output.splitlines()
        result = []
        for line in lines:
            stripped = line.strip()
            if re.match(r'^(ERROR|WARNING|error|warning)', stripped):
                result.append(line)
                continue
            if re.match(r'^\s*Resolved \d+ packages', stripped):
                continue
            if re.match(r'^\s*Installed \d+ packages', stripped):
                continue
            if re.match(r'^\s*Uninstalled \d+ packages', stripped):
                continue
            result.append(line)
        return "\n".join(result)

    def savings_example(self) -> dict:
        return {
            "before": 50,
            "after": 10,
            "description": "uv — dispatches uv run to inner filter, strips uv install noise",
        }
