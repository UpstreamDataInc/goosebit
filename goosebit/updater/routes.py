import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request

from goosebit.settings import TENANT

from . import controller, download
from .manager import get_update_manager_sync


async def verify_tenant(tenant: str):
    if not tenant == TENANT:
        raise HTTPException(404)
    return tenant


async def log_last_connection(request: Request, dev_id: str):
    host = request.client.host
    updater = get_update_manager_sync(dev_id)
    await updater.update_last_ip(host)
    await updater.update_last_seen(round(time.time()))
    await updater.save()


router = APIRouter(
    prefix="/{tenant}",
    dependencies=[Depends(verify_tenant), Depends(log_last_connection)],
    tags=["ddi"],
)
router.include_router(controller.router)
router.include_router(download.router)
