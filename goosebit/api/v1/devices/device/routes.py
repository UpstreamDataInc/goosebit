from __future__ import annotations

from fastapi import APIRouter, Depends, Security
from fastapi.requests import Request

from goosebit.api.v1.devices.device.responses import DeviceLogResponse, DeviceResponse
from goosebit.auth import validate_user_permissions
from goosebit.updater.manager import UpdateManager, get_update_manager

router = APIRouter(prefix="/{dev_id}")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["home.read"])],
)
async def device_get(_: Request, updater: UpdateManager = Depends(get_update_manager)) -> DeviceResponse:
    return await DeviceResponse.convert(await updater.get_device())


@router.get(
    "/log",
    dependencies=[Security(validate_user_permissions, scopes=["home.read"])],
)
async def device_logs(_: Request, updater: UpdateManager = Depends(get_update_manager)) -> DeviceLogResponse:
    device = await updater.get_device()
    return DeviceLogResponse(log=device.last_log)
