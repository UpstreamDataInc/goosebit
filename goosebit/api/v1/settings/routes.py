from fastapi import APIRouter

from . import users

router = APIRouter(prefix="/settings", tags=["settings"])

router.include_router(users.router)
