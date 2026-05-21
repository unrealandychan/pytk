import json
import re
from pytk.filters.base import BaseFilter, cmd_name, strip_ansi


class CurlFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        n = cmd_name(cmd)
        return bool(n) and n in ('curl', 'http', 'https', 'wget')

    def filter(self, output: str, cmd: list[str]) -> str:
        output = strip_ansi(output)
        n = cmd_name(cmd)
        if n == 'wget':
            return self._filter_wget(output)
        elif n in ('http', 'https'):
            return self._filter_httpie(output)
        else:
            return self._filter_curl(output, cmd)

    def _filter_curl(self, output: str, cmd: list[str]) -> str:
        lines = output.splitlines()
        verbose = '-v' in cmd or '--verbose' in cmd

        # Strip progress bar lines
        filtered = []
        for line in lines:
            if re.match(r'^\s*%\s+Total\s+%\s+Received', line):
                continue
            if re.match(r'^\s*\d+\s+\d+', line) and '%' in line:
                continue
            filtered.append(line)
        lines = filtered

        if not verbose:
            body = '\n'.join(lines)
            return self._maybe_truncate_json(body, error=False)

        # Verbose: separate headers from body
        tls_prefixes = ('* TLSv', '* SSL', '* Cipher', '* Trying', '* Connected', '* CAfile', '* using HTTP')
        kept = []
        body_lines = []
        in_body = False
        seen_response = False
        status_code = None

        for line in lines:
            if in_body:
                body_lines.append(line)
                continue
            # Skip TLS noise
            if any(line.startswith(p) for p in tls_prefixes):
                continue
            # Keep response status/headers (lines starting with '<')
            if line.startswith('< HTTP'):
                m = re.search(r'(\d{3})', line)
                if m:
                    status_code = int(m.group(1))
                kept.append(line[2:].strip())
                seen_response = True
                continue
            if line.startswith('<'):
                content = line[2:].strip() if len(line) > 2 else ''
                if seen_response and content == '':
                    # Empty < line signals end of headers, body follows
                    in_body = True
                else:
                    kept.append(content)
                continue
            # Skip other verbose lines (*, >)

        is_error = status_code is not None and status_code >= 400
        body = '\n'.join(body_lines)
        body = self._maybe_truncate_json(body, error=is_error)

        result = '\n'.join(kept)
        if body:
            result = result + '\n\n' + body if result else body
        return result.strip()

    def _maybe_truncate_json(self, body: str, error: bool) -> str:
        stripped = body.strip()
        if stripped.startswith('{') or stripped.startswith('['):
            try:
                parsed = json.loads(stripped)
                pretty = json.dumps(parsed, indent=2)
                lines = pretty.splitlines()
                if not error and len(lines) > 50:
                    remaining = len(lines) - 50
                    lines = lines[:50] + [f'[... {remaining} more lines]']
                return '\n'.join(lines)
            except json.JSONDecodeError:
                lines = stripped.splitlines()
                if not error and len(lines) > 50:
                    remaining = len(lines) - 50
                    lines = lines[:50] + [f'[... {remaining} more lines]']
                return '\n'.join(lines)
        return body

    def _filter_httpie(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        for line in lines:
            if re.match(r'^Elapsed time:', line, re.IGNORECASE):
                continue
            kept.append(line)

        body_start = None
        for i, line in enumerate(kept):
            if line == '' and i > 0:
                body_start = i + 1
                break

        if body_start is not None:
            header_part = '\n'.join(kept[:body_start])
            body_part = '\n'.join(kept[body_start:])
            body_part = self._maybe_truncate_json(body_part, error=False)
            return (header_part + '\n' + body_part).strip()

        return '\n'.join(kept).strip()

    def _filter_wget(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        for line in lines:
            # Skip timestamped wget request lines
            if re.match(r'^--\d{4}-\d{2}-\d{2}', line):
                continue
            # Skip progress bar lines (contain % and [ or dots)
            if re.search(r'\d+%\s*\[', line):
                continue
            if re.search(r'\d+%\s*\.{3,}', line):
                continue
            kept.append(line)
        return '\n'.join(kept).strip()

    def savings_example(self) -> dict:
        return {
            "before": 3000,
            "after": 500,
            "description": "curl -v GET — strips TLS handshake, keeps status/headers/body",
        }
