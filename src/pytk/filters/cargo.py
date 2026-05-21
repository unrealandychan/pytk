import re
from pytk.filters.base import BaseFilter, cmd_name, strip_ansi


class CargoFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        n = cmd_name(cmd)
        return bool(n) and n in ("cargo", "rustc", "rustfmt")

    def filter(self, output: str, cmd: list[str]) -> str:
        output = strip_ansi(output)
        subcmd = cmd[1] if len(cmd) > 1 else ""
        if subcmd in ("build", "check"):
            return self._filter_build(output, {})
        elif subcmd == "test":
            return self._filter_test(output)
        elif subcmd == "clippy":
            return self._filter_clippy(output)
        elif subcmd in ("add", "update"):
            return self._filter_add_update(output)
        elif subcmd == "run":
            return self._filter_run(output)
        return output

    def _filter_build(self, output: str, cfg: dict) -> str:
        lines = output.splitlines()
        max_warnings = cfg.get("max_warnings", 20)
        compiling_count = 0
        kept = []
        warning_count = 0

        # Count compiling lines first
        for line in lines:
            if re.match(r"^\s*Compiling \S+ v[\d.]+", line):
                compiling_count += 1

        for line in lines:
            if re.match(r"^\s*Compiling \S+ v[\d.]+", line):
                continue
            if re.match(r"^\s*Finished (dev|release)", line):
                continue
            if re.match(r"^\s*warning\[", line):
                if warning_count < max_warnings:
                    kept.append(line)
                    warning_count += 1
                continue
            kept.append(line)

        result = []
        if compiling_count > 1:
            result.append(f"Compiling {compiling_count} crates...")
        elif compiling_count == 1:
            result.append("Compiling 1 crate...")

        # Keep errors with 5 lines of context
        error_lines = set()
        for i, line in enumerate(kept):
            if re.search(r"error\[E\d+\]", line):
                for j in range(max(0, i - 5), min(len(kept), i + 6)):
                    error_lines.add(j)

        if error_lines:
            # Add non-error lines (warnings etc.) that aren't already covered
            for i, line in enumerate(kept):
                if i not in error_lines and re.match(r"^\s*warning", line):
                    result.append(line)
            # Add error context in order
            prev = -2
            for i in sorted(error_lines):
                if i > prev + 1 and prev >= 0:
                    result.append("...")
                result.append(kept[i])
                prev = i
        else:
            result.extend(kept)

        return "\n".join(result)

    def _filter_test(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        for line in lines:
            if re.match(r"^\s*test .+ \.\.\. ok\s*$", line):
                continue
            kept.append(line)
        return "\n".join(kept)

    def _filter_clippy(self, output: str) -> str:
        lines = output.splitlines()
        kept = []
        for line in lines:
            if re.match(r"^\s*Checking \S+ v[\d.]+", line):
                continue
            if re.match(r"^\s*= help:", line):
                continue
            kept.append(line)
        return "\n".join(kept)

    def _filter_add_update(self, output: str) -> str:
        lines = output.splitlines()
        added = []
        updated = []
        for line in lines:
            m = re.match(r"^\s*Adding (\S+) v([\d.]+)", line)
            if m:
                added.append(f"{m.group(1)} v{m.group(2)}")
                continue
            m = re.match(r"^\s*Updating (\S+) v[\d.]+ -> v([\d.]+)", line)
            if m:
                updated.append(line.strip())
                continue
            # Also handle simple "Added <crate> v<ver>" lines
            m = re.match(r"^\s*Added? (\S+) v([\d.]+)", line)
            if m:
                added.append(f"{m.group(1)} v{m.group(2)}")
                continue

        result = []
        if added:
            result.append(f"Added {', '.join(added)}")
        if updated:
            if len(updated) == 1:
                result.append(updated[0])
            else:
                result.append(f"Updated {len(updated)} crates")
        if not result:
            # Return non-empty lines
            return "\n".join(l for l in lines if l.strip())
        return "\n".join(result)

    def _filter_run(self, output: str) -> str:
        lines = output.splitlines()
        result = []
        for line in lines:
            if re.match(r'^\s*(Compiling|Finished|Running|Blocking)', line):
                continue
            result.append(line)
        return '\n'.join(result)

    def savings_example(self) -> dict:
        return {
            "before": 5000,
            "after": 300,
            "description": "cargo build (30 crates) — strips Compiling lines, keeps errors",
        }
