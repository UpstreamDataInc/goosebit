from pydantic import BaseModel

from goosebit.schema.users import UserSchema


class SettingsUsersResponse(BaseModel):
    users: list[UserSchema]
