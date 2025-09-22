from __future__ import annotations

from pydantic import BaseModel


class DeviceLogResponse(BaseModel):
    log: str | None
    progress: int | None
