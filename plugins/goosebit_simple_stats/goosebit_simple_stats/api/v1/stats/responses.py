from pydantic import BaseModel


class SimpleStatsResponse(BaseModel):
    software_count: int | None = None
    device_count: int | None = None
