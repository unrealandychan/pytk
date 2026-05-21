import re
from pytk.filters.base import BaseFilter, cmd_name, strip_ansi

MAX_FAILURE_LINES = 10


class TestFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        n = cmd_name(cmd)
        if not n:
            return False
        if n in ("pytest", "jest"):
            return True
        if n in ("npx",) and len(cmd) > 1 and cmd[1] == "jest":
            return True
        if n in ("python", "python3") and len(cmd) > 2 and cmd[1] == "-m" and cmd[2] == "pytest":
            return True
        if n == "go" and len(cmd) > 1 and cmd[1] == "test":
            return True
        if n == "cargo" and len(cmd) > 1 and cmd[1] == "test":
            return True
        if n == "npm" and len(cmd) > 1 and cmd[1] == "test":
            return True
        return False

    def filter(self, output: str, cmd: list[str]) -> str:
        output = strip_ansi(output)
        lines = output.splitlines()
        result = []
        summary_line = None
        in_failure = False
        failure_lines = 0
        failure_block = []

        passing_patterns = [
            re.compile(r'\s+PASSED'),
            re.compile(r'\s+ok$'),
            re.compile(r'^ok\s+'),  # go test ok
            re.compile(r'^\.\s*$'),
            re.compile(r'^[\.]+$'),
            re.compile(r'^\s*\.\s*\.\s*'),
        ]
        summary_patterns = [
            re.compile(r'=+\s+\d+\s+(passed|failed|error)'),
            re.compile(r'\d+\s+passed'),
            re.compile(r'FAILED\s+\d+'),
            re.compile(r'--- FAIL'),
            re.compile(r'test result:'),
        ]
        failure_start_patterns = [
            re.compile(r'^FAILED\s+'),
            re.compile(r'^_{5,}'),  # pytest failure separator
            re.compile(r'^=+\s+FAILURES\s+=+'),
            re.compile(r'^=+\s+ERRORS\s+=+'),
            re.compile(r'--- FAIL:'),
        ]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect summary line
            if any(p.search(line) for p in summary_patterns):
                if not any(p.search(line) for p in failure_start_patterns):
                    summary_line = line
                    i += 1
                    continue

            # Detect failure sections
            if any(p.search(line) for p in failure_start_patterns):
                if failure_block:
                    result.extend(failure_block[:MAX_FAILURE_LINES])
                    failure_block = []
                in_failure = True
                failure_lines = 0
                failure_block.append(line)
                i += 1
                continue

            if in_failure:
                # End of failure block: new separator or blank + next test
                if re.match(r'^=+\s', line) and "FAILED" not in line and "ERROR" not in line:
                    result.extend(failure_block[:MAX_FAILURE_LINES])
                    failure_block = []
                    in_failure = False
                    result.append(line)
                else:
                    failure_block.append(line)
                i += 1
                continue

            # Skip passing lines
            if any(p.search(line) for p in passing_patterns):
                i += 1
                continue

            # Skip empty progress lines
            if line.strip() == "":
                i += 1
                continue

            result.append(line)
            i += 1

        if failure_block:
            result.extend(failure_block[:MAX_FAILURE_LINES])

        if summary_line:
            result.append(summary_line)

        return "\n".join(result)

    def savings_example(self) -> dict:
        return {
            "before": 8000,
            "after": 600,
            "description": "pytest with 100 passing + 2 failing — strips passing, keeps failures + summary",
        }
