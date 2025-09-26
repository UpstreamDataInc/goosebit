from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.requests import Request

from goosebit.api.v1.devices.device.responses import DeviceLogResponse
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db import Device  # type: ignore[attr-defined]
from goosebit.device_manager import get_device
from goosebit.schema.devices import DeviceSchema

router = APIRouter(prefix="/{dev_id}")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["read"]()])],
)
async def device_get(_: Request, device: Device = Depends(get_device)) -> DeviceSchema:
    if device is None:
        raise HTTPException(404)
    await device.fetch_related("assigned_software", "hardware")
    return DeviceSchema.model_validate(device)


@router.get(
    "/log",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["read"]()])],
)
async def device_logs(_: Request, device: Device = Depends(get_device)) -> DeviceLogResponse:
    if device is None:
        raise HTTPException(404)
    return DeviceLogResponse(log=device.last_log, progress=device.progress)
