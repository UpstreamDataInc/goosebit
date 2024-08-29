from __future__ import annotations

from pydantic import BaseModel


class DevicesDeleteRequest(BaseModel):
    devices: list[str]
