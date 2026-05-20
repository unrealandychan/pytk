from pytk.filters.base import BaseFilter

MAX_LINES = 200
HEAD_LINES = 100
TAIL_LINES = 20
MAX_CONSECUTIVE_BLANK = 2


class CatFilter(BaseFilter):
    def matches(self, cmd: list[str]) -> bool:
        return bool(cmd) and cmd[0] in ("cat", "head", "tail", "less", "more")

    def filter(self, output: str, cmd: list[str]) -> str:
        lines = output.splitlines()

        # Strip consecutive blank lines
        cleaned = []
        blank_count = 0
        for line in lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= MAX_CONSECUTIVE_BLANK:
                    cleaned.append(line)
            else:
                blank_count = 0
                cleaned.append(line)

        if len(cleaned) <= MAX_LINES:
            return "\n".join(cleaned)

        # Truncate: first HEAD_LINES + note + last TAIL_LINES
        head = cleaned[:HEAD_LINES]
        tail = cleaned[-TAIL_LINES:]
        truncated = len(cleaned) - HEAD_LINES - TAIL_LINES
        note = f"[... {truncated} lines truncated, use pytk cat --lines N to show more]"
        return "\n".join(head + [note] + tail)

    def savings_example(self) -> dict:
        return {
            "before": 12000,
            "after": 2400,
            "description": "cat on a 300-line file — truncated to head+tail",
        }
