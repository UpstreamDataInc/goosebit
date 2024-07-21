import dataclasses
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal

import semver


@dataclasses.dataclass
class DatetimeVersion:
    timestamp: int

    @classmethod
    def parse(cls, filename: Path, delimiter: str):
        image_data = filename.stem.split(delimiter)
        if len(image_data) == 3:
            _, date, t = image_data
        elif len(image_data) == 4:
            _, _, date, t = image_data
        else:
            raise ValueError(f"Invalid filename: {filename}")

        firmware_date = datetime.strptime(f"{date}_{t}", "%Y%m%d_%H%M%S")

        return cls(timestamp=int(firmware_date.timestamp()))

    def __gt__(self, other):
        return self.timestamp > other.timestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp


@dataclasses.dataclass
class UpdateVersionParser:
    parser: Callable
    delimiter: str

    def parse(self, filename: Path):
        return self.parser(filename=filename, delimiter=self.delimiter)

    @classmethod
    def create(cls, parse_mode: Literal["semantic", "datetime"], delimiter: str):
        if parse_mode == "semantic":
            return cls(parser=semver.parse, delimiter=delimiter)
        if parse_mode == "datetime":
            return cls(parser=DatetimeVersion.parse, delimiter=delimiter)
