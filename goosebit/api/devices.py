from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, Security
from fastapi.requests import Request
from pydantic import BaseModel

from goosebit.auth import validate_user_permissions
from goosebit.models import Device, UpdateModeEnum
from goosebit.permissions import Permissions
from goosebit.updater.manager import delete_device, get_update_manager

router = APIRouter(prefix="/devices")


@router.get(
    "/all",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.HOME.READ])],
)
async def devices_get_all() -> list[dict]:
    devices = await Device.all().prefetch_related("assigned_firmware", "hardware")

    async def parse(device: Device) -> dict:
        manager = await get_update_manager(device.uuid)
        last_seen = device.last_seen
        if last_seen is not None:
            last_seen = round(time.time() - device.last_seen)
        return {
            "uuid": device.uuid,
            "name": device.name,
            "fw": device.fw_version,
            "fw_version": (
                device.assigned_firmware.version
                if device.assigned_firmware is not None
                else None
            ),
            "hw_model": device.hardware.model,
            "hw_revision": device.hardware.revision,
            "feed": device.feed,
            "flavor": device.flavor,
            "progress": device.progress,
            "state": device.last_state,
            "update_mode": str(device.update_mode),
            "force_update": manager.force_update,
            "last_ip": device.last_ip,
            "last_seen": last_seen,
            "online": (
                last_seen < manager.poll_seconds if last_seen is not None else None
            ),
        }

    return list(await asyncio.gather(*[parse(d) for d in devices]))


class UpdateDevicesModel(BaseModel):
    devices: list[str]
    firmware: str | None = None
    name: str | None = None
    pinned: bool = False


@router.post(
    "/update",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.DEVICE.WRITE])
    ],
)
async def devices_update(request: Request, config: UpdateDevicesModel) -> dict:
    for uuid in config.devices:
        updater = await get_update_manager(uuid)
        device = await updater.get_device()
        if config.firmware is not None:
            if config.firmware == "rollout":
                device.update_mode = UpdateModeEnum.ROLLOUT
                device.assigned_firmware_id = None
            elif config.firmware == "latest":
                device.update_mode = UpdateModeEnum.LATEST
                device.assigned_firmware_id = None
            else:
                device.update_mode = UpdateModeEnum.ASSIGNED
                device.assigned_firmware_id = config.firmware
        if config.pinned:
            device.update_mode = UpdateModeEnum.PINNED
            device.assigned_firmware_id = None
        if config.name is not None:
            device.name = config.name
        await updater.save()
    return {"success": True}


class ForceUpdateModel(BaseModel):
    devices: list[str]


@router.post(
    "/force_update",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.DEVICE.WRITE])
    ],
)
async def devices_force_update(request: Request, config: ForceUpdateModel) -> dict:
    for uuid in config.devices:
        updater = await get_update_manager(uuid)
        updater.force_update = True
    return {"success": True}


@router.get(
    "/logs/{dev_id}",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.HOME.READ])],
)
async def device_logs(request: Request, dev_id: str) -> str:
    updater = await get_update_manager(dev_id)
    device = await updater.get_device()
    if device.last_log is not None:
        return device.last_log
    return "No logs found."


class DeleteModel(BaseModel):
    devices: list[str]


@router.post(
    "/delete",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.DEVICE.DELETE])
    ],
)
async def devices_delete(request: Request, config: DeleteModel) -> dict:
    for uuid in config.devices:
        await delete_device(uuid)
    return {"success": True}
