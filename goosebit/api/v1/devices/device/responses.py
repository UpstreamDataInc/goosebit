from __future__ import annotations

from pydantic import BaseModel

from goosebit.schema.devices import DeviceSchema


class DeviceLogResponse(BaseModel):
    log: str | None
    progress: int | None


class DeviceResponse(DeviceSchema):
    pass
