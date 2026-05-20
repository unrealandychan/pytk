import re
from pytk.filters.base import BaseFilter, cmd_name


class PackageManagerFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        if not cmd:
            return False
        n = cmd_name(cmd)
        return bool(n) and n in ("pip", "pip3", "uv", "poetry")

    def filter(self, output: str, cmd: list[str]) -> str:
        lines = output.splitlines()
        result = []
        for line in lines:
            stripped = line.strip()
            # Keep error/warning lines
            if re.match(r'^(ERROR|WARNING|error|warning)', stripped):
                result.append(line)
                continue
            # Keep "Successfully installed" lines
            if stripped.startswith("Successfully installed"):
                result.append(line)
                continue
            # Strip download progress bars containing block chars or progress indicators
            if chr(9601) in line:  # ▁ block char
                continue
            # Strip "Downloading ... %" or lines with progress bars
            if re.search(r'Downloading\s+\S+.*[\d]+%', line):
                continue
            if re.search(r'Downloading\s+\S+.*[▁▂▃▄▅▆▇█━─]+', line):
                continue
            # Strip wheel build noise
            if re.match(r'\s*(Building wheel|Created wheel|Stored in directory)', stripped):
                continue
            result.append(line)
        return "\n".join(result)

    def savings_example(self) -> dict:
        return {
            "before": 300,
            "after": 20,
            "description": "pip install — strips download progress and wheel noise, keeps installed summary",
        }
