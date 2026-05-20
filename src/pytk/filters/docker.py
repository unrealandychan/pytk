import re
from pytk.filters.base import BaseFilter
from pytk.config import load_config, get_filter_config


class DockerFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        return bool(cmd) and cmd[0] in ("docker", "docker-compose")

    def filter(self, output: str, cmd: list[str]) -> str:
        cfg = get_filter_config(load_config(), "docker")
        # determine subcommand (handle "docker compose up" vs "docker-compose up")
        if cmd[0] == "docker" and len(cmd) > 1 and cmd[1] == "compose":
            subcmd = cmd[2] if len(cmd) > 2 else ""
        elif cmd[0] == "docker-compose" and len(cmd) > 1:
            subcmd = cmd[1]
        elif cmd[0] == "docker" and len(cmd) > 1:
            subcmd = cmd[1]
        else:
            subcmd = ""

        if subcmd == "ps":
            return self._filter_ps(output)
        elif subcmd == "images":
            return self._filter_images(output)
        elif subcmd == "logs":
            return self._filter_logs(output, cfg.get("logs_tail", 100))
        elif subcmd == "build":
            return self._filter_build(output)
        elif subcmd in ("up", "down", "start", "stop", "restart"):
            return self._filter_compose_action(output, subcmd)
        return output

    def _filter_ps(self, output: str) -> str:
        """Keep NAME | IMAGE | STATUS, strip CONTAINER ID/COMMAND/CREATED/PORTS columns."""
        lines = output.splitlines()
        result = []
        for line in lines:
            if not line.strip():
                continue
            # header line
            if line.startswith("CONTAINER ID"):
                result.append("NAME   IMAGE   STATUS")
                continue
            # data line: split by 2+ spaces
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 7:
                # docker ps: ID IMAGE COMMAND CREATED STATUS PORTS NAMES
                name = parts[6] if len(parts) > 6 else parts[-1]
                image = parts[1]
                status = parts[4]
                result.append(f"{name}   {image}   {status}")
            else:
                result.append(line)
        return "\n".join(result)

    def _filter_images(self, output: str) -> str:
        """Keep REPOSITORY:TAG only."""
        lines = output.splitlines()
        result = []
        for line in lines:
            if not line.strip():
                continue
            if line.startswith("REPOSITORY"):
                result.append("REPOSITORY:TAG")
                continue
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 2:
                repo = parts[0]
                tag = parts[1]
                result.append(f"{repo}:{tag}" if tag != "<none>" else repo)
            else:
                result.append(line)
        return "\n".join(result)

    def _filter_logs(self, output: str, tail: int = 100) -> str:
        """Strip ANSI, truncate to last N lines, deduplicate repeated lines."""
        # strip ANSI escape codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean = ansi_escape.sub('', output)
        lines = clean.splitlines()
        # truncate to tail
        if len(lines) > tail:
            lines = lines[-tail:]
        # deduplicate consecutive repeated lines
        deduped = []
        i = 0
        while i < len(lines):
            line = lines[i]
            count = 1
            while i + count < len(lines) and lines[i + count] == line:
                count += 1
            if count > 3:
                deduped.append(line)
                deduped.append(f"[repeated {count - 1} more times]")
            else:
                deduped.extend(lines[i:i+count])
            i += count
        return "\n".join(deduped)

    def _filter_build(self, output: str) -> str:
        """Strip step/cache lines, keep errors and final image ID."""
        lines = output.splitlines()
        result = []
        error_mode = False
        for line in lines:
            stripped = line.strip()
            # Skip progress/step/cache lines
            if re.match(r'^Step \d+/\d+ :', line):
                continue
            if stripped.startswith("---> Using cache"):
                continue
            if stripped.startswith("---> Running in"):
                continue
            if re.match(r'^Sending build context', line):
                continue
            if re.match(r'^\s*#\d+\s+\[', line):  # BuildKit layer lines
                continue
            if re.match(r'^\s*#\d+\s+DONE', line):
                continue
            if re.match(r'^\s*#\d+\s+[0-9.]+s', line):
                continue
            # Keep errors
            if "error" in stripped.lower() or "Error" in stripped:
                error_mode = True
            if error_mode:
                result.append(line)
                continue
            # Keep final success line
            if stripped.startswith("Successfully built") or stripped.startswith("Successfully tagged"):
                result.append(stripped)
                continue
            # Keep exporting/writing lines (final stages)
            if stripped.startswith("writing image") or stripped.startswith("exporting"):
                continue
        return "\n".join(result) if result else output.splitlines()[-1] if output.strip() else ""

    def _filter_compose_action(self, output: str, subcmd: str) -> str:
        """Compress compose up/down to service name + status."""
        lines = output.splitlines()
        result = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Strip pull progress bars: "Pulling from ...", download percentage lines
            if re.match(r'^[a-f0-9]+:\s+(Pull|Push|Download|Extract|Waiting|Verifying)', stripped):
                continue
            if re.match(r'^Pulling\s+\w+\s+\.\.\.', stripped):
                continue
            # Keep: "Creating/Starting/Stopping/Removing service_name ... done"
            m = re.match(r'^(Creating|Starting|Stopping|Removing|Recreating)\s+(\S+)\s*\.\.\.\s*(done|error|failed)?', stripped)
            if m:
                status = m.group(3) or "..."
                result.append(f"{m.group(2)}: {m.group(1).lower()} {status}")
                continue
            # Keep error lines
            if "error" in stripped.lower() or "ERROR" in stripped:
                result.append(stripped)
                continue
            # Keep final "Network ... created" type lines
            if re.match(r'^Network\s+\S+\s+Created', stripped):
                result.append(stripped)
                continue
        return "\n".join(result) if result else output.strip()

    def savings_example(self) -> dict:
        return {
            "before": 3000,
            "after": 300,
            "description": "docker build (30 steps) — strips step/cache lines, keeps errors and final ID",
        }
