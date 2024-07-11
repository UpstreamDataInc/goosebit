from fastapi import APIRouter

from . import revision

router = APIRouter(prefix="/controller")
router.include_router(revision.router)
