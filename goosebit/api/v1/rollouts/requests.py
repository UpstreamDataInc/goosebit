from pydantic import BaseModel, Field


class RolloutsPutRequest(BaseModel):
    name: str
    feed: str
    software_id: int
    max_timeouts: int | None = Field(default=None, ge=0)


class RolloutsPatchRequest(BaseModel):
    ids: list[int]
    paused: bool


class RolloutsDeleteRequest(BaseModel):
    ids: list[int]
