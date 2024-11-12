from __future__ import annotations

from pydantic import BaseModel


class DevicesDeleteRequest(BaseModel):
    devices: list[str]


class DevicesPatchRequest(BaseModel):
    devices: list[str]
    software: str | None = None
    name: str | None = None
    pinned: bool | None = None
    feed: str | None = None
    force_update: bool | None = None
    auth_token: str | None = None


class DevicesPutRequest(BaseModel):
    devices: list[str]
    software: str | None = None
    name: str | None = None
    pinned: bool | None = None
    feed: str | None = None
    force_update: bool | None = None
    auth_token: str | None = None
