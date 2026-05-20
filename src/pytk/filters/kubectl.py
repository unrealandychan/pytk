import re
import json
from pytk.filters.base import BaseFilter, cmd_name


class KubectlFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        n = cmd_name(cmd)
        return bool(n) and n in ('kubectl', 'k')

    def filter(self, output: str, cmd: list[str]) -> str:
        if len(cmd) < 2:
            return output
        subcmd = cmd[1]
        if subcmd == 'get':
            # Check if next arg is 'events'
            if len(cmd) > 2 and cmd[2] == 'events':
                return self._filter_events(output)
            return self._filter_get(output, cmd)
        elif subcmd == 'describe':
            return self._filter_describe(output)
        elif subcmd == 'logs':
            return self._filter_logs(output)
        elif subcmd in ('apply', 'delete', 'create', 'patch'):
            return self._filter_action(output)
        elif subcmd == 'rollout':
            return self._filter_rollout(output)
        return output

    def _filter_get(self, output: str, cmd: list[str]) -> str:
        cmd_lower = [c.lower() for c in cmd]
        if 'events' in cmd_lower:
            return self._filter_events(output)
        if 'pods' in cmd_lower or 'pod' in cmd_lower:
            return self._filter_get_pods(output)
        lines = output.splitlines()
        return '\n'.join(lines[:50])

    def _filter_get_pods(self, output: str) -> str:
        """Keep NAME STATUS RESTARTS AGE columns only."""
        lines = output.splitlines()
        result = []
        name_col = status_col = restarts_col = age_col = None

        for i, line in enumerate(lines):
            if i == 0 and 'NAME' in line:
                # Parse header to find column positions
                header = line
                name_col = header.index('NAME')
                status_col = header.index('STATUS') if 'STATUS' in header else None
                restarts_col = header.index('RESTARTS') if 'RESTARTS' in header else None
                age_col = header.index('AGE') if 'AGE' in header else None
                result.append('NAME   STATUS   RESTARTS   AGE')
                continue
            if not line.strip():
                continue
            if name_col is not None and status_col is not None:
                parts = re.split(r'\s{2,}', line.strip())
                # For wide output: NAME READY STATUS RESTARTS AGE IP NODE ...
                # Detect if READY column exists (header has READY)
                if 'READY' in lines[0]:
                    # NAME READY STATUS RESTARTS AGE [IP NODE ...]
                    if len(parts) >= 5:
                        result.append(f'{parts[0]}   {parts[2]}   {parts[3]}   {parts[4]}')
                    else:
                        result.append(line)
                else:
                    # NAME STATUS RESTARTS AGE
                    if len(parts) >= 4:
                        result.append(f'{parts[0]}   {parts[1]}   {parts[2]}   {parts[3]}')
                    else:
                        result.append(line)
            else:
                result.append(line)
        return '\n'.join(result)

    def _filter_describe(self, output: str) -> str:
        lines = output.splitlines()
        result = []
        skip_block = False
        in_events = False
        events_header_idx = None
        events_lines = []
        pre_events = []

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Detect Events section
            if re.match(r'^Events:', line):
                in_events = True
                events_header_idx = len(pre_events)
                events_lines.append(line)
                i += 1
                continue

            if in_events:
                events_lines.append(line)
                i += 1
                continue

            # Skip Annotations block
            if re.match(r'^Annotations:', line):
                skip_block = True
                i += 1
                continue

            # Skip Labels block
            if re.match(r'^Labels:', line):
                skip_block = True
                i += 1
                continue

            # End of skipped block: next line that doesn't start with whitespace
            if skip_block:
                if stripped and not line.startswith(' ') and not line.startswith('\t'):
                    skip_block = False
                    # fall through to process this line
                else:
                    i += 1
                    continue

            pre_events.append(line)
            i += 1

        # Decide whether to include events
        has_warning = any('Warning' in l for l in events_lines)
        result = pre_events
        if has_warning and events_lines:
            result = result + events_lines

        return '\n'.join(result)

    def _filter_logs(self, output: str) -> str:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean = ansi_escape.sub('', output)
        lines = clean.splitlines()
        if len(lines) > 100:
            lines = lines[-100:]
        # Deduplicate consecutive repeated lines
        deduped = []
        i = 0
        while i < len(lines):
            line = lines[i]
            count = 1
            while i + count < len(lines) and lines[i + count] == line:
                count += 1
            if count > 3:
                deduped.append(line)
                deduped.append(f'[repeated {count - 1} more times]')
            else:
                deduped.extend(lines[i:i + count])
            i += count
        # Try JSON log extraction
        result = []
        for line in deduped:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    extracted = {}
                    for key in ('level', 'severity'):
                        if key in obj:
                            extracted[key] = obj[key]
                            break
                    for key in ('msg', 'message'):
                        if key in obj:
                            extracted[key] = obj[key]
                            break
                    for key in ('error', 'err'):
                        if key in obj:
                            extracted[key] = obj[key]
                            break
                    result.append(json.dumps(extracted))
                else:
                    result.append(line)
            except (json.JSONDecodeError, ValueError):
                result.append(line)
        return '\n'.join(result)

    def _filter_events(self, output: str) -> str:
        lines = output.splitlines()
        result = []
        header_line = None
        type_col = None

        for i, line in enumerate(lines):
            if i == 0 and 'LAST SEEN' in line:
                header_line = line
                result.append(line)
                type_col = line.index('TYPE') if 'TYPE' in line else None
                continue
            if not line.strip():
                continue
            # Check TYPE column value
            if type_col is not None:
                # Extract the TYPE field by splitting
                parts = re.split(r'\s{2,}', line.strip())
                # Find TYPE column - it's after LAST SEEN
                # Use positional split on header
                if header_line:
                    header_parts = re.split(r'\s{2,}', header_line.strip())
                    try:
                        type_idx = header_parts.index('TYPE')
                        if len(parts) > type_idx:
                            if parts[type_idx] == 'Warning':
                                result.append(line)
                        # Skip Normal rows
                    except ValueError:
                        result.append(line)
                else:
                    result.append(line)
            else:
                result.append(line)
        return '\n'.join(result)

    def _filter_action(self, output: str) -> str:
        lines = output.splitlines()
        result = [l for l in lines if l.strip()]
        return '\n'.join(result)

    def _filter_rollout(self, output: str) -> str:
        lines = [l for l in output.splitlines() if l.strip()]
        if lines:
            return lines[-1]
        return output

    def savings_example(self) -> dict:
        return {
            'before': 3000,
            'after': 400,
            'description': 'kubectl describe pod — strips annotations/labels/normal events',
        }
