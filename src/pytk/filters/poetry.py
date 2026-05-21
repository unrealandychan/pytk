import re
from pytk.filters.base import BaseFilter, cmd_name, strip_ansi


class PoetryFilter(BaseFilter):
    def matches(self, cmd):
        n = cmd_name(cmd)
        return bool(n) and n == 'poetry'

    def filter(self, output, cmd):
        output = strip_ansi(output)
        subcmd = cmd[1] if len(cmd) > 1 else ''
        if subcmd == 'run' and len(cmd) > 2:
            inner = cmd[2:]
            from pytk.filters.registry import get_filter
            inner_filt = get_filter(inner)
            if inner_filt is not None:
                return inner_filt.filter(output, inner)
        if subcmd in ('install', 'add', 'remove', 'update', 'lock'):
            return self._filter_install(output)
        return output

    def _filter_install(self, output):
        lines = output.splitlines()
        result = []
        for line in lines:
            if re.search(r'(error|Error|warning|Warning|Installing|Updating|Removing|Package operations)', line):
                result.append(line)
        if not result:
            non_empty = [l for l in lines if l.strip()]
            return non_empty[-1] if non_empty else output
        return '\n'.join(result)

    def savings_example(self):
        return {'before': 3000, 'after': 400, 'description': 'poetry install — keeps only package operation summary'}
