from __future__ import annotations

from fastapi import APIRouter

from . import stats

router = APIRouter(prefix="/v1")
router.include_router(stats.router)
