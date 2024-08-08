from pydantic import BaseModel


class StatusResponse(BaseModel):
    success: bool
