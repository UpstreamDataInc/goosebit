from fastapi import APIRouter, Depends

from goosebit.auth import validate_current_user

from . import telemetry, v1

router = APIRouter(prefix="/api", dependencies=[Depends(validate_current_user)])
router.include_router(telemetry.router)  # type: ignore[attr-defined]
router.include_router(v1.router)  # type: ignore[attr-defined]
