import time

from fastapi import APIRouter, Depends
from fastapi.requests import Request

from goosebit.device_manager import get_update_manager
from goosebit.settings import config

from . import controller


async def log_last_connection(request: Request, dev_id: str):
    updater = await get_update_manager(dev_id)
    if config.track_device_ip:
        await updater.update_last_connection(round(time.time()), request.client.host)
    else:
        await updater.update_last_connection(round(time.time()))


router = APIRouter(
    prefix="/ddi",
    dependencies=[Depends(log_last_connection)],
    tags=["ddi"],
)
router.include_router(controller.router)
