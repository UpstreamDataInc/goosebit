from fastapi import APIRouter

from . import v1

router = APIRouter(prefix="/controller")
router.include_router(v1.router)
