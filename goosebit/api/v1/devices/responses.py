from __future__ import annotations

from pydantic import BaseModel

from goosebit.schema.devices import DeviceSchema


class DevicesResponse(BaseModel):
    devices: list[DeviceSchema]
