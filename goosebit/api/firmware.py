import semver
from fastapi import APIRouter, Body, Security
from fastapi.requests import Request

from goosebit.auth import validate_user_permissions
from goosebit.models import FirmwareUpdate
from goosebit.permissions import Permissions
from goosebit.settings import UPDATES_DIR

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
        firmware.append(
            {
                "name": update.path.name,
                "size": update.path.stat().st_size,
                "version": update.version,
            }
        )
    return firmware


@router.post(
    "/delete",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.DELETE])
    ],
)
async def firmware_delete(request: Request, file: str = Body()) -> dict:
    file_path = UPDATES_DIR.joinpath(file)
    if file_path.exists():
        file_path.unlink()
        return {"success": True}
    return {"success": False}
