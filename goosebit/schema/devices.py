from __future__ import annotations

import time
from enum import Enum, IntEnum, StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, computed_field

from goosebit.db.models import Device, UpdateModeEnum, UpdateStateEnum
from goosebit.updater.manager import get_update_manager


class ConvertableEnum(StrEnum):
    @classmethod
    def convert(cls, value: IntEnum):
        return cls(str(value))


def enum_factory(name: str, base: type[Enum]) -> type[ConvertableEnum]:
    enum_dict = {item.name: str(item) for item in base}
    return ConvertableEnum(name, enum_dict)  # type: ignore


UpdateStateSchema = enum_factory("UpdateStateSchema", UpdateStateEnum)
UpdateModeSchema = enum_factory("UpdateModeSchema", UpdateModeEnum)


class DeviceSchema(BaseModel):
    uuid: str
    name: str | None
    sw_version: str | None
    sw_target_version: str | None
    sw_assigned: int | None
    hw_model: str
    hw_revision: str
    feed: str
    progress: int | None
    last_state: Annotated[UpdateStateSchema, BeforeValidator(UpdateStateSchema.convert)]
    update_mode: Annotated[UpdateModeSchema, BeforeValidator(UpdateModeSchema.convert)]
    force_update: bool
    last_ip: str | None
    last_seen: int | None
    poll_seconds: int

    @computed_field
    def online(self) -> bool | None:
        return self.last_seen < self.poll_seconds if self.last_seen is not None else None

    @classmethod
    async def convert(cls, device: Device):
        manager = await get_update_manager(device.uuid)
        _, target_software = await manager.get_update()
        last_seen = device.last_seen
        if last_seen is not None:
            last_seen = round(time.time() - device.last_seen)

        return cls(
            uuid=device.uuid,
            name=device.name,
            sw_version=device.sw_version,
            sw_target_version=(target_software.version if target_software is not None else None),
            sw_assigned=(device.assigned_software.id if device.assigned_software is not None else None),
            hw_model=device.hardware.model,
            hw_revision=device.hardware.revision,
            feed=device.feed,
            progress=device.progress,
            last_state=device.last_state,
            update_mode=device.update_mode,
            force_update=device.force_update,
            last_ip=device.last_ip,
            last_seen=last_seen,
            poll_seconds=manager.poll_seconds,
        )
