from pydantic import BaseModel


class RolloutsPutRequest(BaseModel):
    name: str
    feed: str
    software_id: int


class RolloutsPatchRequest(BaseModel):
    ids: list[int]
    paused: bool


class RolloutsDeleteRequest(BaseModel):
    ids: list[int]
