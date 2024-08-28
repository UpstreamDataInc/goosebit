from __future__ import annotations

from pydantic import BaseModel

from goosebit.db.models import Rollout


class RolloutSchema(BaseModel):
    id: int
    created_at: int
    name: str | None
    feed: str
    sw_file: str
    sw_version: str
    paused: bool
    success_count: int
    failure_count: int

    @classmethod
    async def convert(cls, rollout: Rollout):
        return cls(
            id=rollout.id,
            created_at=int(rollout.created_at.timestamp() * 1000),
            name=rollout.name,
            feed=rollout.feed,
            sw_file=rollout.software.path.name,
            sw_version=rollout.software.version,
            paused=rollout.paused,
            success_count=rollout.success_count,
            failure_count=rollout.failure_count,
        )
