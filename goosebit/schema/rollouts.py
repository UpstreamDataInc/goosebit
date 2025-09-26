from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer

from goosebit.schema.software import SoftwareSchema


class RolloutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    name: str | None
    feed: str
    software: SoftwareSchema
    paused: bool
    success_count: int
    failure_count: int

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime, _info: Any) -> int:
        return int(created_at.timestamp() * 1000)
