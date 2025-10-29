from fastapi import APIRouter

from goosebit.auth.permissions import HANDLER, Permission

from . import users

router = APIRouter(prefix="/settings", tags=["settings"])

router.include_router(users.router)  # type: ignore[attr-defined]


@router.get("/permissions", response_model_exclude_none=True)
async def settings_permissions_get() -> list[Permission]:
    return HANDLER.permissions
