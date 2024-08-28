from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.auth import validate_user_permissions
from goosebit.db.models import Device, UpdateModeEnum, UpdateStateEnum

from .responses import BFFDeviceResponse

router = APIRouter(prefix="/devices")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["home.read"])],
)
async def devices_get(request: Request) -> BFFDeviceResponse:
    def search_filter(search_value):
        return (
            Q(uuid__icontains=search_value)
            | Q(name__icontains=search_value)
            | Q(feed__icontains=search_value)
            | Q(sw_version__icontains=search_value)
            | Q(update_mode=int(UpdateModeEnum.from_str(search_value)))
            | Q(last_state=int(UpdateStateEnum.from_str(search_value)))
        )

    query = Device.all().prefetch_related("assigned_software", "hardware")
    total_records = await Device.all().count()

    return await BFFDeviceResponse.convert(request, query, search_filter, total_records)
