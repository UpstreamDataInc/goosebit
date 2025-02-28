from __future__ import annotations

from fastapi import APIRouter

from . import example

router = APIRouter(prefix="/v1")
router.include_router(example.router)
