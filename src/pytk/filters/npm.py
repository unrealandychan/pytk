import re
from pytk.filters.base import BaseFilter, cmd_name, strip_ansi


class NpmFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        n = cmd_name(cmd)
        return bool(n) and n in ('npm', 'yarn', 'pnpm', 'npx')

    def filter(self, output: str, cmd: list[str]) -> str:
        output = strip_ansi(output)
        subcmd = cmd[1] if len(cmd) > 1 else ''
        n = cmd_name(cmd)
        tool = n

        # npx is its own dispatch
        if tool == 'npx':
            return self._filter_npx(output)

        if subcmd in ('install', 'i', 'add', 'ci'):
            return self._filter_install(output)
        elif subcmd in ('run', 'build', 'start', 'dev', 'serve'):
            return self._filter_run(output)
        elif subcmd == 'audit':
            return self._filter_audit(output)
        elif subcmd in ('test', 'jest', 'vitest'):
            return self._filter_test(output)
        return output

    def _filter_install(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        for line in lines:
            stripped = line.strip()
            # Progress/spinner lines (e.g. ⸨░░░░⸩ ⠴ reify:lodash or ████ 50%)
            if re.search(r'[⸨⸩░▓█⠴⠦⠧⠇⠏⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]', line):
                continue
            # Lines like 'npm http fetch', 'npm timing', 'npm verb'
            if re.match(r'^npm (http|timing|verb|silly|info reify|info run|WARN engine)', line):
                continue
            # Progress percent lines
            if re.match(r'^\s*[\[|]\s*[=\s>]*[\]|]\s*\d+%', line):
                continue
            # Yarn progress lines like "[1/4] Resolving packages..."
            if re.match(r'^\[[\d/]+\]\s', line):
                continue
            # pnpm progress lines
            if re.match(r'^Packages:\s+\+\d', line) and 'added' not in line.lower():
                pass  # keep package count lines
            kept.append(line)
        return '\n'.join(kept).strip()

    def _filter_run(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        for line in lines:
            # Strip '> project@version script' header lines
            if re.match(r'^>\s+\S+@\S+\s+\S+', line):
                continue
            # Strip '> command' lines that follow the header
            if re.match(r'^>\s+\S', line) and not kept:
                continue
            # Strip webpack/vite/rollup progress lines like '[====] 80%' or 'Building... 75%'
            if re.search(r'\[=+\s*>?\s*\]\s*\d+%', line):
                continue
            if re.match(r'^.*(Building|Compiling|Bundling).*\d+%', line):
                continue
            kept.append(line)
        # Strip leading/trailing blank lines
        while kept and not kept[0].strip():
            kept.pop(0)
        while kept and not kept[-1].strip():
            kept.pop()
        return '\n'.join(kept)

    def _filter_audit(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        for line in lines:
            stripped = line.strip()
            # Keep vulnerability summary lines
            if re.search(r'found \d+ vulnerabilit', line, re.IGNORECASE):
                kept.append(line)
            # Keep 'run npm audit fix' suggestion
            elif re.search(r'run `?npm audit fix`?', line, re.IGNORECASE):
                kept.append(line)
            # Keep severity summary lines
            elif re.match(r'^(critical|high|moderate|low|info)\s+\d+', stripped, re.IGNORECASE):
                kept.append(line)
        return '\n'.join(kept).strip()

    def _filter_test(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        for line in lines:
            # Strip passing test lines
            if ' PASS ' in line or '✓' in line or '✔' in line:
                continue
            kept.append(line)
        return '\n'.join(kept).strip()

    def _filter_npx(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        skip_next = False
        for line in lines:
            if 'Need to install the following packages:' in line:
                skip_next = True
                continue
            if skip_next:
                # Skip the package name lines and blank separator
                if line.strip() == '' or re.match(r'^\s+\S', line):
                    continue
                # Check for 'Ok to proceed?' prompt line
                if re.search(r'Ok to proceed\?', line):
                    skip_next = False
                    continue
                skip_next = False
            kept.append(line)
        return '\n'.join(kept).strip()

    def savings_example(self) -> dict:
        return {
            'before': 5000,
            'after': 300,
            'description': 'npm install (100 packages) — strips progress bars',
        }
