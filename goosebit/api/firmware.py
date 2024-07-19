from fastapi import APIRouter, Body, Security
from fastapi.requests import Request

from goosebit.auth import validate_user_permissions
from goosebit.permissions import Permissions
from goosebit.settings import UPDATES_DIR
from goosebit.updater.misc import fw_sort_key
from goosebit.updates.artifacts import FirmwareArtifact

router = APIRouter(prefix="/firmware")


@router.get(
    "/all",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])
    ],
)
async def firmware_get_all() -> list[dict]:
    UPDATES_DIR.mkdir(parents=True, exist_ok=True)

    firmware = []
    for file in sorted(
        [f for f in UPDATES_DIR.iterdir() if f.suffix == ".swu"],
        key=lambda x: fw_sort_key(x),
        reverse=True,
    ):
        artifact = FirmwareArtifact(file.name)
        firmware.append(
            {
                "name": file.name,
                "size": artifact.path.stat().st_size,
                "version": artifact.version,
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
