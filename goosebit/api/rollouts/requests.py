from pydantic import BaseModel


class CreateRolloutsRequest(BaseModel):
    name: str
    feed: str
    firmware_id: int


class UpdateRolloutsRequest(BaseModel):
    ids: list[int]
    paused: bool


class DeleteRolloutsRequest(BaseModel):
    ids: list[int]
