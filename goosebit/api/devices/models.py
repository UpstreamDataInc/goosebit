from __future__ import annotations

import asyncio
import time
from enum import StrEnum
from typing import Annotated

from fastapi.requests import Request
from pydantic import BaseModel, BeforeValidator, Field, computed_field

from goosebit.models import Device, UpdateModeEnum, UpdateStateEnum
from goosebit.updater.manager import get_update_manager


class DeviceTableResponse(BaseModel):
    data: list[DeviceModel]
    draw: int
    records_total: int = Field(serialization_alias="recordsTotal")
    records_filtered: int = Field(serialization_alias="recordsFiltered")

    @classmethod
    async def parse(cls, request: Request, query, search_filter, total_records):
        params = request.query_params

        draw = int(params.get("draw", 1))
        start = int(params.get("start", 0))
        length = int(params.get("length", 10))
        search_value = params.get("search[value]", None)
        order_column_index = params.get("order[0][column]", None)
        order_column = params.get(f"columns[{order_column_index}][data]", None)
        order_dir = params.get("order[0][dir]", None)

        if search_value:
            query = query.filter(search_filter(search_value))

        if order_column:
            query = query.order_by(f"{"-" if order_dir == "desc" else ""}{order_column}")

        filtered_records = await query.count()
        devices = await query.offset(start).limit(length).all()
        data = list(await asyncio.gather(*[DeviceModel.parse(d) for d in devices]))

        return cls(data=data, draw=draw, records_total=total_records, records_filtered=filtered_records)


class DeviceAllResponse(BaseModel):
    devices: list[DeviceModel]

    @classmethod
    async def parse(cls, devices: list[Device]):
        return cls(devices=await asyncio.gather(*[DeviceModel.parse(d) for d in devices]))


class UpdateDevicesRequest(BaseModel):
    devices: list[str]
    firmware: str | None = None
    name: str | None = None
    pinned: bool | None = None
    feed: str | None = None


class LogsDeviceResponse(BaseModel):
    log: str | None


class DeleteDevicesRequest(BaseModel):
    devices: list[str]


class ForceUpdateDevicesRequest(BaseModel):
    devices: list[str]


class UpdateStateModel(StrEnum):
    NONE = str(UpdateStateEnum.NONE)
    UNKNOWN = str(UpdateStateEnum.UNKNOWN)
    REGISTERED = str(UpdateStateEnum.REGISTERED)
    RUNNING = str(UpdateStateEnum.RUNNING)
    ERROR = str(UpdateStateEnum.ERROR)
    FINISHED = str(UpdateStateEnum.FINISHED)

    @classmethod
    def parse(cls, update_state: UpdateStateEnum):
        return cls(str(update_state))


class UpdateModeModel(StrEnum):
    NONE = str(UpdateModeEnum.NONE)
    LATEST = str(UpdateModeEnum.LATEST)
    PINNED = str(UpdateModeEnum.PINNED)
    ROLLOUT = str(UpdateModeEnum.ROLLOUT)
    ASSIGNED = str(UpdateModeEnum.ASSIGNED)

    @classmethod
    def parse(cls, update_mode: UpdateModeEnum):
        return cls(str(update_mode))


class DeviceModel(BaseModel):
    uuid: str
    name: str | None
    fw_installed_version: str | None
    fw_target_version: str | None
    fw_assigned: str | None
    hw_model: str
    hw_revision: str
    feed: str
    progress: int | None
    state: Annotated[UpdateStateModel, BeforeValidator(UpdateStateModel.parse)]
    update_mode: Annotated[UpdateModeModel, BeforeValidator(UpdateModeModel.parse)]
    force_update: bool
    last_ip: str | None
    last_seen: int | None
    poll_seconds: int

    @computed_field
    def online(self) -> bool | None:
        return self.last_seen < self.poll_seconds if self.last_seen is not None else None

    @classmethod
    async def parse(cls, device: Device):
        manager = await get_update_manager(device.uuid)
        _, target_firmware = await manager.get_update()
        last_seen = device.last_seen
        if last_seen is not None:
            last_seen = round(time.time() - device.last_seen)

        return cls(
            uuid=device.uuid,
            name=device.name,
            fw_installed_version=device.fw_version,
            fw_target_version=(target_firmware.version if target_firmware is not None else None),
            fw_assigned=(device.assigned_firmware.id if device.assigned_firmware is not None else None),
            hw_model=device.hardware.model,
            hw_revision=device.hardware.revision,
            feed=device.feed,
            progress=device.progress,
            state=device.last_state,
            update_mode=device.update_mode,
            force_update=device.force_update,
            last_ip=device.last_ip,
            last_seen=last_seen,
            poll_seconds=manager.poll_seconds,
        )
