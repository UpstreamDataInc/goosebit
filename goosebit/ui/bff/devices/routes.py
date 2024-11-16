from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.api.responses import StatusResponse
from goosebit.api.v1.devices import routes
from goosebit.auth import validate_user_permissions
from goosebit.db.models import Device, Software, UpdateModeEnum, UpdateStateEnum
from goosebit.device_manager import get_update_manager
from goosebit.schema.devices import DeviceSchema
from goosebit.schema.software import SoftwareSchema
from goosebit.settings import config
from goosebit.ui.bff.common.requests import DataTableRequest
from goosebit.ui.bff.common.util import parse_datatables_query

from ..common.responses import DTColumnDescription, DTColumns
from .requests import DevicesPatchRequest
from .responses import BFFDeviceResponse

router = APIRouter(prefix="/devices")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["device.read"])],
)
async def devices_get(dt_query: Annotated[DataTableRequest, Depends(parse_datatables_query)]) -> BFFDeviceResponse:
    def search_filter(search_value: str):
        return (
            Q(uuid__icontains=search_value)
            | Q(name__icontains=search_value)
            | Q(feed__icontains=search_value)
            | Q(sw_version__icontains=search_value)
            | Q(update_mode=int(UpdateModeEnum.from_str(search_value)))
            | Q(last_state=int(UpdateStateEnum.from_str(search_value)))
        )

    query = Device.all().prefetch_related("assigned_software", "hardware", "assigned_software__compatibility")

    response = await BFFDeviceResponse.convert(dt_query, query, search_filter)

    async def set_assigned_sw(d: DeviceSchema):
        updater = await get_update_manager(d.uuid)
        _, target = await updater.get_update()
        if target is not None:
            await target.fetch_related("compatibility")
            d.assigned_software = SoftwareSchema.model_validate(target)
        return d

    response.data = await asyncio.gather(*[set_assigned_sw(d) for d in response.data])
    return response


@router.patch(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["device.write"])],
)
async def devices_patch(_: Request, config: DevicesPatchRequest) -> StatusResponse:
    for uuid in config.devices:
        updater = await get_update_manager(uuid)
        if config.software is not None:
            if config.software == "rollout":
                await updater.update_update(UpdateModeEnum.ROLLOUT, None)
            elif config.software == "latest":
                await updater.update_update(UpdateModeEnum.LATEST, None)
            else:
                software = await Software.get_or_none(id=config.software)
                await updater.update_update(UpdateModeEnum.ASSIGNED, software)
        if config.pinned is not None:
            await updater.update_update(UpdateModeEnum.PINNED, None)
        if config.name is not None:
            await updater.update_name(config.name)
        if config.feed is not None:
            await updater.update_feed(config.feed)
        if config.force_update is not None:
            await updater.update_force_update(config.force_update)
    return StatusResponse(success=True)


router.add_api_route(
    "",
    routes.devices_delete,
    methods=["DELETE"],
    dependencies=[Security(validate_user_permissions, scopes=["device.delete"])],
    name="bff_devices_delete",
)


@router.get(
    "/columns",
    dependencies=[Security(validate_user_permissions, scopes=["device.read"])],
    response_model_exclude_none=True,
)
async def devices_get_columns() -> DTColumns:
    columns = []
    columns.append(DTColumnDescription(title="Online", data="online"))
    columns.append(DTColumnDescription(title="UUID", data="uuid", name="uuid", searchable=True, orderable=True))
    columns.append(DTColumnDescription(title="Name", data="name", name="name", searchable=True, orderable=True))
    columns.append(DTColumnDescription(title="Model", data="hw_model"))
    columns.append(DTColumnDescription(title="Revision", data="hw_revision"))
    columns.append(DTColumnDescription(title="Feed", data="feed", name="feed", searchable=True, orderable=True))
    columns.append(
        DTColumnDescription(
            title="Installed Software", data="sw_version", name="sw_version", searchable=True, orderable=True
        )
    )
    columns.append(DTColumnDescription(title="Target Software", data="sw_target_version"))
    columns.append(
        DTColumnDescription(
            title="Update Mode", data="update_mode", name="update_mode", searchable=True, orderable=True
        )
    )
    columns.append(
        DTColumnDescription(title="State", data="last_state", name="last_state", searchable=True, orderable=True)
    )
    columns.append(DTColumnDescription(title="Force Update", data="force_update"))
    columns.append(DTColumnDescription(title="Progress", data="progress"))
    if config.track_device_ip:
        columns.append(DTColumnDescription(title="Last IP", data="last_ip"))
    columns.append(DTColumnDescription(title="Last Seen", data="last_seen"))
    return DTColumns(columns=columns)
