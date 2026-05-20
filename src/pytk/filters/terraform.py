import re
from pytk.filters.base import BaseFilter


class TerraformFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        return bool(cmd) and cmd[0] == "terraform"

    def filter(self, output: str, cmd: list[str]) -> str:
        lines = output.splitlines()
        result = []
        for line in lines:
            stripped = line.strip()
            # Strip "Refreshing state..." lines
            if "Refreshing state..." in line:
                continue
            # Strip download progress lines (for init)
            if re.match(r'^\s*-\s+.*\.\.\.', line) and not re.search(r'(Initializing|Error|Warning)', line):
                # heuristic: init download lines like "- Installing hashicorp/aws v4.0.0..."
                if re.match(r'^\s*-\s+(Installing|Downloading|Installed)', line):
                    continue
            # Strip bare progress/dots lines
            if re.match(r'^\s*\.+\s*$', line):
                continue
            result.append(line)
        return "\n".join(result)

    def savings_example(self) -> dict:
        return {
            "before": 500,
            "after": 100,
            "description": "terraform apply — strips refresh/progress noise, keeps plan and errors",
        }
