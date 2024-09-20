from __future__ import annotations

from pydantic import BaseModel

from goosebit.api.responses import StatusResponse
from goosebit.schema.rollouts import RolloutSchema


class RolloutsPutResponse(StatusResponse):
    id: int | None = None


class RolloutsResponse(BaseModel):
    rollouts: list[RolloutSchema]
