import time
from typing import Optional

READONLY_PREFIXES = {"git", "ls", "find", "tree", "cat", "head", "tail", "grep", "rg", "ag"}
DEFAULT_TTL = 30  # seconds

_cache: dict = {}  # {(cmd, cwd): (timestamp, output)}


def is_cacheable(command: str) -> bool:
    first = command.strip().split()[0] if command.strip() else ""
    return first in READONLY_PREFIXES


def get(command: str, cwd: str, ttl: int = DEFAULT_TTL) -> Optional[str]:
    key = (command, cwd)
    if key in _cache:
        ts, output = _cache[key]
        if time.time() - ts < ttl:
            return output
        del _cache[key]
    return None


def set(command: str, cwd: str, output: str) -> None:
    _cache[(command, cwd)] = (time.time(), output)


def clear() -> None:
    _cache.clear()


def size() -> int:
    return len(_cache)
