from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer

from goosebit.schema.software import SoftwareSchema


class RolloutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    name: str | None
    feed: str
    software: SoftwareSchema = Field(exclude=True)
    paused: bool
    success_count: int
    failure_count: int

    @computed_field  # type: ignore[misc]
    @property
    def sw_version(self) -> str:
        return self.software.version

    @computed_field  # type: ignore[misc]
    @property
    def sw_file(self) -> str:
        return self.software.path.name

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime, _info):
        return int(created_at.timestamp() * 1000)
