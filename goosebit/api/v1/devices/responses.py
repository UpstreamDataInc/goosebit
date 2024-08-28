from __future__ import annotations

import asyncio

from pydantic import BaseModel

from goosebit.db.models import Device
from goosebit.schema.devices import DeviceSchema


class DevicesResponse(BaseModel):
    devices: list[DeviceSchema]

    @classmethod
    async def convert(cls, devices: list[Device]):
        return cls(devices=await asyncio.gather(*[DeviceSchema.convert(d) for d in devices]))
