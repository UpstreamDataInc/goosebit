from __future__ import annotations

from fastapi import APIRouter

from . import devices, firmware, rollouts

router = APIRouter(prefix="/bff", tags=["bff"])
router.include_router(devices.router)
router.include_router(firmware.router)
router.include_router(rollouts.router)
