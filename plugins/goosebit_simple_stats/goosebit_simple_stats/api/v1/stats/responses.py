from pydantic import BaseModel


class ExampleResponse(BaseModel):
    software_count: int | None = None
    device_count: int | None = None
