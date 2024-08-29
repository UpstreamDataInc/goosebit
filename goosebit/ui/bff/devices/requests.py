from __future__ import annotations

from pydantic import BaseModel


class DevicesPatchRequest(BaseModel):
    devices: list[str]
    software: str | None = None
    name: str | None = None
    pinned: bool | None = None
    feed: str | None = None
    force_update: bool | None = None
