from __future__ import annotations

from fastapi import APIRouter

from . import devices, download, rollouts, software

router = APIRouter(prefix="/bff", tags=["bff"])
router.include_router(devices.router)
router.include_router(software.router)
router.include_router(rollouts.router)
router.include_router(download.router)
