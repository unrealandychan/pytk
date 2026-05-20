from pytk.filters.ls import LsFilter
from pytk.filters.git import GitFilter
from pytk.filters.test import TestFilter
from pytk.filters.grep import GrepFilter
from pytk.filters.cat import CatFilter
from pytk.filters.docker import DockerFilter
from pytk.filters.base import BaseFilter

FILTERS: list[BaseFilter] = [LsFilter(), GitFilter(), TestFilter(), GrepFilter(), CatFilter(), DockerFilter()]


def get_filter(cmd: list[str]) -> BaseFilter | None:
    for f in FILTERS:
        if f.matches(cmd):
            return f
    return None
