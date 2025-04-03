from fastapi import APIRouter

from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS, Permission

from . import users

router = APIRouter(prefix="/settings", tags=["settings"])

router.include_router(users.router)


@router.get("/permissions", response_model_exclude_none=True)
async def settings_permissions_get() -> Permission:
    return GOOSEBIT_PERMISSIONS
