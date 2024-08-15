from __future__ import annotations

from fastapi import APIRouter

from . import devices, firmware

router = APIRouter(prefix="/bff", tags=["bff"], include_in_schema=True)
router.include_router(devices.router)
router.include_router(firmware.router)
