from __future__ import annotations

import asyncio

from pydantic import BaseModel

from goosebit.models import Firmware, Hardware


class HardwareSchema(BaseModel):
    id: int
    model: str
    revision: str

    @classmethod
    async def convert(cls, hardware: Hardware):
        return cls(id=hardware.id, model=hardware.model, revision=hardware.revision)


class FirmwareSchema(BaseModel):
    id: int
    name: str
    size: int
    hash: str
    version: str
    compatibility: list[HardwareSchema]

    @classmethod
    async def convert(cls, firmware: Firmware):
        return cls(
            id=firmware.id,
            name=firmware.path_user,
            size=firmware.size,
            hash=firmware.hash,
            version=firmware.version,
            compatibility=await asyncio.gather(*[HardwareSchema.convert(h) for h in firmware.compatibility]),
        )
