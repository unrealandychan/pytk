import re
from pytk.filters.base import BaseFilter, cmd_name, strip_ansi


class MakeFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        n = cmd_name(cmd)
        return bool(n) and n in ("make",)

    def filter(self, output: str, cmd: list[str]) -> str:
        output = strip_ansi(output)
        lines = output.splitlines()
        result = []
        for line in lines:
            # Remove make directory enter/leave messages
            if re.match(r'^make\[.*\]: (Entering|Leaving) directory', line):
                continue
            # Remove command echoes (lines starting with a tab)
            if line.startswith('\t'):
                continue
            result.append(line)
        return "\n".join(result)

    def savings_example(self) -> dict:
        return {
            "before": 200,
            "after": 50,
            "description": "make build — strips directory enter/leave and command echoes",
        }
