from pydantic import BaseModel


class SoftwareDeleteRequest(BaseModel):
    files: list[int]
