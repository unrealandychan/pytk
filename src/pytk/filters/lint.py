import re
from pytk.filters.base import BaseFilter, cmd_name, strip_ansi


class LintFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        n = cmd_name(cmd)
        return bool(n) and n in ('ruff', 'mypy', 'flake8', 'pylint', 'tsc', 'pyright')

    def filter(self, output: str, cmd: list[str]) -> str:
        output = strip_ansi(output)
        n = cmd_name(cmd)
        if n == 'ruff':
            return self._filter_ruff(output)
        elif n == 'mypy':
            return self._filter_mypy(output)
        elif n in ('flake8', 'pyright'):
            return self._filter_flake8(output)
        elif n == 'pylint':
            return self._filter_pylint(output)
        elif n == 'tsc':
            return self._filter_tsc(output)
        return output

    def _filter_ruff(self, output: str) -> str:
        lines = output.splitlines()
        result = []
        for line in lines:
            # Skip "All checks passed" clean run lines
            if re.match(r'^All checks passed', line):
                continue
            # Skip blank lines
            if not line.strip():
                continue
            result.append(line)
        if not result:
            return 'ruff: no issues found'
        return '\n'.join(result)

    def _filter_mypy(self, output: str) -> str:
        lines = output.splitlines()
        result = []
        for line in lines:
            # Keep error/warning/note lines (file:line:col: level: message)
            if re.match(r'^.*:\d+: (error|warning|note):', line):
                result.append(line)
            # Keep summary line
            elif re.match(r'^Found \d+ error', line) or re.match(r'^Success:', line):
                result.append(line)
        if not result:
            return 'mypy: no issues found'
        return '\n'.join(result)

    def _filter_flake8(self, output: str) -> str:
        # flake8 only outputs error lines, so just strip blanks
        lines = [l for l in output.splitlines() if l.strip()]
        if not lines:
            return 'flake8: no issues found'
        return '\n'.join(lines)

    def _filter_pylint(self, output: str) -> str:
        lines = output.splitlines()
        result = []
        for line in lines:
            # Keep C/W/E/R/F message lines
            if re.match(r'^.*:\d+:\d+: [CWERF]\d+:', line):
                result.append(line)
            # Keep rating/summary line
            elif 'rated at' in line or 'Your code has been rated' in line:
                result.append(line)
            elif re.match(r'^-+$', line):
                continue
        if not result:
            return 'pylint: no issues found'
        return '\n'.join(result)

    def _filter_tsc(self, output: str) -> str:
        lines = output.splitlines()
        result = []
        for line in lines:
            # Keep error lines: file(line,col): error TS...
            if re.match(r'^.+\(\d+,\d+\): error TS', line):
                result.append(line)
            elif 'error TS' in line:
                result.append(line)
        if not result:
            return 'tsc: no errors'
        return '\n'.join(result)

    def savings_example(self) -> dict:
        return {
            'before': 5000,
            'after': 200,
            'description': 'ruff check on 50 files — strips passing output, keeps only violations',
        }
