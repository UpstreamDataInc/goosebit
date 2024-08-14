from __future__ import annotations

from pydantic import BaseModel

from goosebit.models import Firmware, Hardware


class HardwareSchema(BaseModel):
    id: int
    model: str
    revision: str

    @classmethod
    def parse(cls, hardware: Hardware):
        return cls(id=hardware.id, model=hardware.model, revision=hardware.revision)


class FirmwareSchema(BaseModel):
    id: int
    name: str
    size: int
    hash: str
    version: str
    compatibility: list[HardwareSchema]

    @classmethod
    async def parse(cls, firmware: Firmware):
        return cls(
            id=firmware.id,
            name=firmware.path_user,
            size=firmware.size,
            hash=firmware.hash,
            version=firmware.version,
            compatibility=[HardwareSchema.parse(h) for h in firmware.compatibility],
        )
