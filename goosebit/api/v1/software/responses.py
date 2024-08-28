from __future__ import annotations

import asyncio

from pydantic import BaseModel

from goosebit.db.models import Software
from goosebit.schema.software import SoftwareSchema


class SoftwareResponse(BaseModel):
    software: list[SoftwareSchema]

    @classmethod
    async def convert(cls, software: list[Software]):
        return cls(software=await asyncio.gather(*[SoftwareSchema.convert(f) for f in software]))
