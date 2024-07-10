from fastapi import APIRouter, Depends

from goosebit.auth import authenticate_ws_session

from . import logs

router = APIRouter(
    prefix="/realtime",
    dependencies=[Depends(authenticate_ws_session)],
    tags=["realtime"],
)

router.include_router(logs.router)
