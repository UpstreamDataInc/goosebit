from fastapi import APIRouter, Depends

from goosebit.auth import Authentication

from . import telemetry, v1

router = APIRouter(prefix="/api", dependencies=[Depends(Authentication())])
router.include_router(telemetry.router)
router.include_router(v1.router)
