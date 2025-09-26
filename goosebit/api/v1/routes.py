from fastapi import APIRouter

from . import devices, download, rollouts, settings, software

router = APIRouter(prefix="/v1")
router.include_router(software.router)  # type: ignore[attr-defined]
router.include_router(devices.router)  # type: ignore[attr-defined]
router.include_router(rollouts.router)  # type: ignore[attr-defined]
router.include_router(download.router)  # type: ignore[attr-defined]
router.include_router(settings.router)  # type: ignore[attr-defined]
