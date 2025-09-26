from __future__ import annotations

import time
from datetime import datetime
from enum import Enum, IntEnum, StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, computed_field

from goosebit.db.models import UpdateModeEnum, UpdateStateEnum
from goosebit.schema.software import HardwareSchema, SoftwareSchema
from goosebit.settings import config


class ConvertableEnum(StrEnum):
    @classmethod
    def convert(cls, value: IntEnum) -> ConvertableEnum:
        return cls(str(value))


def enum_factory(name: str, base: type[Enum]) -> type[ConvertableEnum]:
    enum_dict = {item.name: str(item) for item in base}
    return ConvertableEnum(name, enum_dict)  # type: ignore


UpdateStateSchema = enum_factory("UpdateStateSchema", UpdateStateEnum)
UpdateModeSchema = enum_factory("UpdateModeSchema", UpdateModeEnum)


class DeviceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str | None
    sw_version: str | None

    assigned_software: SoftwareSchema | None
    hardware: HardwareSchema | None

    feed: str | None
    progress: int | None
    last_state: Annotated[UpdateStateSchema, BeforeValidator(UpdateStateSchema.convert)]  # type: ignore[valid-type]
    update_mode: Annotated[UpdateModeSchema, BeforeValidator(UpdateModeSchema.convert)]  # type: ignore[valid-type]
    force_update: bool
    last_ip: str | None
    last_seen: Annotated[
        int | None, BeforeValidator(lambda last_seen: round(time.time() - last_seen) if last_seen is not None else None)
    ]
    auth_token: str | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def polling(self) -> bool | None:
        return self.last_seen < (self.poll_seconds + 10) if self.last_seen is not None else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def poll_seconds(self) -> int:
        time_obj = datetime.strptime(config.poll_time, "%H:%M:%S")
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
