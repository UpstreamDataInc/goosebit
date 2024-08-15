from __future__ import annotations

import asyncio

from pydantic import BaseModel

from goosebit.models import Firmware
from goosebit.schema.firmware import FirmwareSchema


class FirmwareResponse(BaseModel):
    firmware: list[FirmwareSchema]

    @classmethod
    async def convert(cls, firmware: list[Firmware]):
        return cls(firmware=await asyncio.gather(*[FirmwareSchema.convert(f) for f in firmware]))
