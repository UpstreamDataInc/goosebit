from __future__ import annotations

import asyncio

from pydantic import BaseModel

from goosebit.models import Device
from goosebit.schema.devices import DeviceSchema


class DeviceResponse(BaseModel):
    devices: list[DeviceSchema]

    @classmethod
    async def convert(cls, devices: list[Device]):
        return cls(devices=await asyncio.gather(*[DeviceSchema.convert(d) for d in devices]))


class LogsDeviceResponse(BaseModel):
    log: str | None
