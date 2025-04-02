from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request

from goosebit.api.v1.settings.users.responses import SettingsUsersResponse
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db.models import User

router = APIRouter(prefix="/users")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["settings"]["users"]["read"]()])],
)
async def settings_users_get(_: Request) -> SettingsUsersResponse:
    users = await User.all()
    return SettingsUsersResponse(users=users)
