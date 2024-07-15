from fastapi import APIRouter, Depends

from goosebit.api import devices, download, firmware, rollouts
from goosebit.auth import authenticate_api_session

router = APIRouter(
    prefix="/api", dependencies=[Depends(authenticate_api_session)], tags=["api"]
)
router.include_router(firmware.router)
router.include_router(devices.router)
router.include_router(rollouts.router)
router.include_router(download.router)
