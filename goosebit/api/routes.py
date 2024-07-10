from fastapi import APIRouter, Depends

from goosebit.api import devices, download, firmware
from goosebit.auth import authenticate_api_session

router = APIRouter(
    prefix="/api", dependencies=[Depends(authenticate_api_session)], tags=["api"]
)
router.include_router(firmware.router)
router.include_router(devices.router)
router.include_router(download.router)
