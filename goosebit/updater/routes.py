import time

from fastapi import APIRouter, Depends

from . import controller
from .manager import get_update_manager


async def log_last_connection(dev_id: str):
    updater = await get_update_manager(dev_id)
    await updater.update_last_connection(round(time.time()))


router = APIRouter(
    prefix="/ddi",
    dependencies=[Depends(log_last_connection)],
    tags=["ddi"],
)
router.include_router(controller.router)
