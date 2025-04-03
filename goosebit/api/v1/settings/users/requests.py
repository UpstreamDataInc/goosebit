from pydantic import BaseModel


class UsersPutRequest(BaseModel):
    username: str
    password: str
    permissions: list[str]


class UsersPatchRequest(BaseModel):
    usernames: list[str]
    enabled: bool


class UsersDeleteRequest(BaseModel):
    usernames: list[str]
