from fastapi import APIRouter

from . import users

router = APIRouter(prefix="/settings")

router.include_router(users.router)
