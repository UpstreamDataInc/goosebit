from __future__ import annotations

from fastapi import APIRouter, Depends

from goosebit.auth import validate_current_user

from . import devices, download, rollouts, settings, software

router = APIRouter(prefix="/bff", tags=["bff"], dependencies=[Depends(validate_current_user)])
router.include_router(devices.router)
router.include_router(software.router)
router.include_router(rollouts.router)
router.include_router(download.router)
router.include_router(settings.router)
