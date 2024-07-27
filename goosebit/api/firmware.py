import semver
from fastapi import APIRouter, Body, Security
from fastapi.requests import Request

from goosebit.auth import validate_user_permissions
from goosebit.models import Firmware
from goosebit.permissions import Permissions

router = APIRouter(prefix="/firmware")


@router.get(
    "/all",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])
    ],
)
async def firmware_get_all() -> list[dict]:
    firmwares = await Firmware.all()
    result = []
    for f in sorted(
        firmwares,
        key=lambda x: semver.Version.parse(x.version),
        reverse=True,
    ):
        result.append(
            {
                "id": f.id,
                "name": f.path.name,
                "size": f.size,
                "hash": f.hash,
                "version": f.version,
                "compatibility": list(await f.compatibility.all().values()),
            }
        )
    return result


@router.post(
    "/delete",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.DELETE])
    ],
)
async def firmware_delete(request: Request, files: list[str] = Body()) -> dict:
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
