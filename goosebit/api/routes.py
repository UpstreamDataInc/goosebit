from fastapi import APIRouter, Depends

from goosebit.api import devices, download, firmware, rollouts
from goosebit.auth import authenticate_api_session

# main router that requires authentication
main_router = APIRouter(prefix="/api", dependencies=[Depends(authenticate_api_session)], tags=["api"])
main_router.include_router(firmware.router)
main_router.include_router(devices.router)
main_router.include_router(rollouts.router)

# download router without authentication
download_router = APIRouter(prefix="/api", tags=["api"])
download_router.include_router(download.router)

# include both routers
router = APIRouter()
router.include_router(main_router)
router.include_router(download_router)
