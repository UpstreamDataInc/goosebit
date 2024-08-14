from __future__ import annotations

from pydantic import BaseModel

from goosebit.models import Rollout


class RolloutSchema(BaseModel):
    id: int
    created_at: int
    name: str | None
    feed: str
    fw_file: str
    fw_version: str
    paused: bool
    success_count: int
    failure_count: int

    @classmethod
    def parse(cls, rollout: Rollout):
        return cls(
            id=rollout.id,
            created_at=int(rollout.created_at.timestamp() * 1000),
            name=rollout.name,
            feed=rollout.feed,
            fw_file=rollout.firmware.path.name,
            fw_version=rollout.firmware.version,
            paused=rollout.paused,
            success_count=rollout.success_count,
            failure_count=rollout.failure_count,
        )
