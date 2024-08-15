from __future__ import annotations

from pydantic import BaseModel


class DevicesDeleteRequest(BaseModel):
    devices: list[str]


class ForceUpdateDevicesRequest(BaseModel):
    devices: list[str]


class DevicesPatchRequest(BaseModel):
    devices: list[str]
    firmware: str | None = None
    name: str | None = None
    pinned: bool | None = None
    feed: str | None = None
