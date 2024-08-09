from pydantic import BaseModel


class DeleteFirmwareRequest(BaseModel):
    files: list[int]
