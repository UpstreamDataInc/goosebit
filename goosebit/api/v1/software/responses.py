from __future__ import annotations

from pydantic import BaseModel

from goosebit.schema.software import SoftwareSchema


class SoftwareResponse(BaseModel):
    software: list[SoftwareSchema]
