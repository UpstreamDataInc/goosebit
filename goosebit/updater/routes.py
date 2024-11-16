import time

from fastapi import APIRouter, Depends
from fastapi.requests import Request

from goosebit.device_manager import DeviceManager, get_device
from goosebit.settings import config

from . import controller


async def log_last_connection(request: Request, dev_id: str):
    device = await get_device(dev_id)
    if config.track_device_ip:
        await DeviceManager.update_last_connection(device, round(time.time()), request.client.host)
    else:
        await DeviceManager.update_last_connection(device, round(time.time()))


router = APIRouter(
    prefix="/ddi",
    dependencies=[Depends(log_last_connection)],
    tags=["ddi"],
)
router.include_router(controller.router)
