from __future__ import annotations

import asyncio

from pydantic import BaseModel

from goosebit.db.models import Hardware, Software


class HardwareSchema(BaseModel):
    id: int
    model: str
    revision: str

    @classmethod
    async def convert(cls, hardware: Hardware):
        return cls(id=hardware.id, model=hardware.model, revision=hardware.revision)


class SoftwareSchema(BaseModel):
    id: int
    name: str
    size: int
    hash: str
    version: str
    compatibility: list[HardwareSchema]

    @classmethod
    async def convert(cls, software: Software):
        return cls(
            id=software.id,
            name=software.path_user,
            size=software.size,
            hash=software.hash,
            version=software.version,
            compatibility=await asyncio.gather(*[HardwareSchema.convert(h) for h in software.compatibility]),
        )
