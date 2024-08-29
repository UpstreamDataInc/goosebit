from pydantic import BaseModel


class SoftwareDeleteRequest(BaseModel):
    software_ids: list[int]
