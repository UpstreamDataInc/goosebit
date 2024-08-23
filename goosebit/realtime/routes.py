from fastapi import APIRouter, Depends

from goosebit.auth import validate_current_user

from . import logs

router = APIRouter(
    prefix="/realtime",
    dependencies=[Depends(validate_current_user)],
    tags=["realtime"],
)

router.include_router(logs.router)
