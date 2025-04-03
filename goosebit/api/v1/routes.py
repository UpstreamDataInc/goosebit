from fastapi import APIRouter

from . import devices, download, rollouts, settings, software

router = APIRouter(prefix="/v1")
router.include_router(software.router)
router.include_router(devices.router)
router.include_router(rollouts.router)
router.include_router(download.router)
router.include_router(settings.router)
