from abc import ABC, abstractmethod


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
