from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.auth import validate_user_permissions
from goosebit.models import Firmware
from goosebit.permissions import Permissions
from goosebit.ui.bff.firmware.responses import BFFFirmwareResponse

router = APIRouter(prefix="/firmware")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])],
)
async def firmware_get(request: Request) -> BFFFirmwareResponse:
    def search_filter(search_value):
        return Q(uri__icontains=search_value) | Q(version__icontains=search_value)

    query = Firmware.all().prefetch_related("compatibility")
    total_records = await Firmware.all().count()

    return await BFFFirmwareResponse.convert(request, query, search_filter, total_records)
