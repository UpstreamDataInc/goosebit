from __future__ import annotations

from pydantic import BaseModel

from goosebit.models import Firmware, Hardware


class HardwareModel(BaseModel):
    id: int
    model: str
    revision: str

    @classmethod
    def parse(cls, hardware: Hardware):
        return cls(id=hardware.id, model=hardware.model, revision=hardware.revision)


class FirmwareModel(BaseModel):
    id: int
    name: str
    size: int
    hash: str
    version: str
    compatibility: list[HardwareModel]

    @classmethod
    async def parse(cls, firmware: Firmware):
        return cls(
            id=firmware.id,
            name=firmware.path_user,
            size=firmware.size,
            hash=firmware.hash,
            version=firmware.version,
            compatibility=[HardwareModel.parse(h) for h in firmware.compatibility],
        )
