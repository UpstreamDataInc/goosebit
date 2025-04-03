from __future__ import annotations

from fastapi import APIRouter, HTTPException, Security
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db.models import User
from goosebit.users import UserManager, create_user

from .requests import UsersDeleteRequest, UsersPatchRequest, UsersPutRequest
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


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["settings"]["users"]["delete"]()])],
)
async def settings_users_delete(_: Request, config: UsersDeleteRequest) -> StatusResponse:
    await UserManager.delete_users(config.usernames)
    return StatusResponse(success=True)


@router.patch(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["settings"]["users"]["delete"]()])],
)
async def settings_users_patch(_: Request, config: UsersPatchRequest) -> StatusResponse:
    for username in config.usernames:
        if await User.get_or_none(username=username) is None:
            raise HTTPException(404, f"User with username {username} not found")

        user = await UserManager.get_user(username)
        await UserManager.update_enabled(user, config.enabled)
    return StatusResponse(success=True)
