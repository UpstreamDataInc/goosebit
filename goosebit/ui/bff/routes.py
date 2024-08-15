from __future__ import annotations

from fastapi import APIRouter

from . import devices

router = APIRouter(prefix="/bff", tags=["bff"], include_in_schema=True)
router.include_router(devices.router)
