import asyncio

from pydantic import BaseModel

from goosebit.api.responses import StatusResponse
from goosebit.db.models import Rollout
from goosebit.schema.rollouts import RolloutSchema


class RolloutsPutResponse(StatusResponse):
    id: int


class RolloutsResponse(BaseModel):
    rollouts: list[RolloutSchema]

    @classmethod
    async def convert(cls, devices: list[Rollout]):
        return cls(rollouts=await asyncio.gather(*[RolloutSchema.convert(d) for d in devices]))
