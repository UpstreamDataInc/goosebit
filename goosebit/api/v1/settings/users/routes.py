from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db.models import User
from goosebit.users import create_user

from .requests import UsersPutRequest
from .responses import SettingsUsersResponse

router = APIRouter(prefix="/users")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["settings"]["users"]["read"]()])],
)
async def settings_users_get(_: Request) -> SettingsUsersResponse:
    users = await User.all()
    return SettingsUsersResponse(users=users)


@router.post(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["settings"]["users"]["write"]()])],
)
async def settings_users_put(_: Request, user: UsersPutRequest) -> StatusResponse:
    await create_user(username=user.username, password=user.password, permissions=user.permissions)
    return StatusResponse(success=True)
