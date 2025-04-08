from pydantic import BaseModel, ConfigDict


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    enabled: bool
    permissions: list[str]
