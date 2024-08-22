from pydantic import BaseModel


class FirmwareDeleteRequest(BaseModel):
    files: list[int]
