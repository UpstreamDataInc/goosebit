import semver
from fastapi import APIRouter, Body, Security
from fastapi.requests import Request

from goosebit.auth import validate_user_permissions
from goosebit.models import FirmwareUpdate
from goosebit.permissions import Permissions

router = APIRouter(prefix="/firmware")


@router.get(
    "/all",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])
    ],
)
async def firmware_get_all() -> list[dict]:
    updates = await FirmwareUpdate.all()
    firmware = []
    for update in sorted(
        updates,
        key=lambda x: semver.Version.parse(x.version),
        reverse=True,
    ):
        for i in range(100):
            firmware.append(
                {
                    "uuid": update.id,
                    "name": update.path.name,
                    "size": update.path.stat().st_size,
                    "version": update.version,
                    "compatibility": list(await update.compatibility.all().values()),
                }
            )
    return firmware


@router.post(
    "/delete",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.DELETE])
    ],
)
async def firmware_delete(request: Request, files: list[str] = Body()) -> dict:
    success = False
    for f_id in files:
        update = await FirmwareUpdate.get_or_none(id=f_id)
        if update is None:
            continue
        path = update.path
        if path.exists():
            path.unlink()
            await update.delete()
            success = True
    return {"success": success}
