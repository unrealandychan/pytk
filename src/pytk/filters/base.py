from abc import ABC, abstractmethod
import os
import re

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*[mKHFABCDJsurh]')


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return _ANSI_RE.sub('', text)


def cmd_name(cmd: list[str]) -> str:
    """Return the basename of cmd[0], stripping full paths.

    Handles cases like '/usr/bin/python3' -> 'python3',
    '/home/user/.venv/bin/pytest' -> 'pytest', 'python' -> 'python'.
    """
    if not cmd:
        return ""
    return os.path.basename(cmd[0])


class BaseFilter(ABC):
    @abstractmethod
    def matches(self, cmd: list[str]) -> bool:
        """Return True if this filter handles the command."""

    @abstractmethod
    def filter(self, output: str, cmd: list[str]) -> str:
        """Filter/compress the command output."""

    def savings_example(self) -> dict:
        """Return {'before': N, 'after': N, 'description': str} for pytk list-filters."""
        return {}
