from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.api.responses import StatusResponse
from goosebit.api.v1.devices import routes
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db.models import Device, Software, UpdateModeEnum, UpdateStateEnum
from goosebit.device_manager import DeviceManager, get_device
from goosebit.schema.devices import DeviceSchema
from goosebit.schema.software import SoftwareSchema
from goosebit.ui.bff.common.requests import DataTableRequest
from goosebit.ui.bff.common.util import parse_datatables_query

from ..common.columns import DeviceColumns
from ..common.responses import DTColumns
from . import device
from .requests import DevicesPatchRequest
from .responses import BFFDeviceResponse

router = APIRouter(prefix="/devices")
router.include_router(device.router)


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["read"]()])],
)
async def devices_get(dt_query: Annotated[DataTableRequest, Depends(parse_datatables_query)]) -> BFFDeviceResponse:
    def search_filter(search_value: str):
        return (
            Q(id__icontains=search_value)
            | Q(name__icontains=search_value)
            | Q(feed__icontains=search_value)
            | Q(sw_version__icontains=search_value)
            | Q(update_mode=int(UpdateModeEnum.from_str(search_value)))
            | Q(last_state=int(UpdateStateEnum.from_str(search_value)))
        )

    query = Device.all().prefetch_related("assigned_software", "hardware", "assigned_software__compatibility")

    response = await BFFDeviceResponse.convert(dt_query, query, search_filter)

    async def set_assigned_sw(d: DeviceSchema):
        device = await get_device(d.id)
        _, target = await DeviceManager.get_update(device)
        if target is not None:
            await target.fetch_related("compatibility")
            d.assigned_software = SoftwareSchema.model_validate(target)
        return d

    response.data = await asyncio.gather(*[set_assigned_sw(d) for d in response.data])
    return response


@router.patch(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["write"]()])],
)
async def devices_patch(_: Request, config: DevicesPatchRequest) -> StatusResponse:
    for dev_id in config.devices:
        if await Device.get_or_none(id=dev_id) is None:
            raise HTTPException(404, f"Device with ID {dev_id} not found")
        device = await get_device(dev_id)
        if config.feed is not None:
            await DeviceManager.update_feed(device, config.feed)
        if config.software is not None:
            if config.software == "rollout":
                await DeviceManager.update_update(device, UpdateModeEnum.ROLLOUT, None)
            elif config.software == "latest":
                await DeviceManager.update_update(device, UpdateModeEnum.LATEST, None)
            else:
                software = await Software.get_or_none(id=config.software)
                await DeviceManager.update_update(device, UpdateModeEnum.ASSIGNED, software)
        if config.pinned is not None:
            await DeviceManager.update_update(device, UpdateModeEnum.PINNED, None)
        if config.name is not None:
            await DeviceManager.update_name(device, config.name)
        if config.force_update is not None:
            await DeviceManager.update_force_update(device, config.force_update)
        if config.auth_token is not None:
            await DeviceManager.update_auth_token(device, config.auth_token)
    return StatusResponse(success=True)


router.add_api_route(
    "",
    routes.devices_delete,
    methods=["DELETE"],
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["delete"]()])],
    name="bff_devices_delete",
)


@router.get(
    "/columns",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["read"]()])],
    response_model_exclude_none=True,
)
async def devices_get_columns(request: Request) -> DTColumns:
    config = request.scope["config"]
    columns = list(
        filter(
            None,
            [
                DeviceColumns.id,
                DeviceColumns.name,
                DeviceColumns.hw_model,
                DeviceColumns.hw_revision,
                DeviceColumns.feed,
                DeviceColumns.sw_version,
                DeviceColumns.sw_target_version,
                DeviceColumns.update_mode,
                DeviceColumns.last_state,
                DeviceColumns.force_update,
                DeviceColumns.progress,
                DeviceColumns.last_ip if config.track_device_ip else None,
                DeviceColumns.polling,
                DeviceColumns.last_seen,
            ],
        )
    )
    return DTColumns(columns=columns)
