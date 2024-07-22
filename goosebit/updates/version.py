import dataclasses
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal

from semver import Version as SemanticVersion


@dataclasses.dataclass
class DatetimeVersion:
    timestamp: int

    @classmethod
    def parse(cls, version: str):
        firmware_date = datetime.strptime(version, "%Y%m%d-%H%M%S")
        return cls(timestamp=int(firmware_date.timestamp()))

    def __gt__(self, other):
        return self.timestamp > other.timestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp


@dataclasses.dataclass
class UpdateVersionParser:
    parser: Callable

    def parse(self, filename: Path):
        _, _, version = filename.stem.split("_")
        return self.parser(version)

    @classmethod
    def create(cls, parse_mode: Literal["semantic", "datetime"]):
        if parse_mode == "semantic":
            return cls(parser=SemanticVersion.parse)
        if parse_mode == "datetime":
            return cls(parser=DatetimeVersion.parse)
