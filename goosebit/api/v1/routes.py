from fastapi import APIRouter

from . import devices, download, firmware, rollouts

router = APIRouter(prefix="/v1")
router.include_router(firmware.router)
router.include_router(devices.router)
router.include_router(rollouts.router)
router.include_router(download.router)
