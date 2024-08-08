from fastapi import APIRouter, Depends

from goosebit.auth import Authentication

from . import logs

router = APIRouter(
    prefix="/realtime",
    dependencies=[Depends(Authentication())],
    tags=["realtime"],
)

router.include_router(logs.router)
