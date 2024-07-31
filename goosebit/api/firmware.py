from typing import Any

from fastapi import APIRouter, Body, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.api.helper import filter_data
from goosebit.auth import validate_user_permissions
from goosebit.models import Firmware
from goosebit.permissions import Permissions

router = APIRouter(prefix="/firmware")


@router.get(
    "/all",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])],
)
async def firmware_get_all(
    request: Request,
) -> dict[str, int | list[dict[str, list[Any] | Any]]]:
    query = Firmware.all()

    def search_filter(search_value):
        return Q(uri__icontains=search_value) | Q(version__icontains=search_value)

    async def parse(f):
        return {
            "id": f.id,
            "name": f.path.name,
            "size": f.size,
            "hash": f.hash,
            "version": f.version,
            "compatibility": list(await f.compatibility.all().values()),
        }

    total_records = await Firmware.all().count()
    return await filter_data(request, query, search_filter, parse, total_records)


@router.post(
    "/delete",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.DELETE])],
)
async def firmware_delete(_: Request, files: list[int] = Body()) -> dict:
    success = False
    for f_id in files:
        firmware = await Firmware.get_or_none(id=f_id)
        if firmware is None:
            continue
        if firmware.local:
            path = firmware.path
            if path.exists():
                path.unlink()
        await firmware.delete()
        success = True
    return {"success": success}
