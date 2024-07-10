from fastapi import APIRouter, Security
from fastapi.requests import Request
from fastapi.responses import FileResponse

from goosebit.auth import validate_user_permissions
from goosebit.permissions import Permissions
from goosebit.settings import UPDATES_DIR

router = APIRouter(prefix="/download")


@router.get(
    "/{file}",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])
    ],
)
async def download_file(request: Request, file: str):
    filename = UPDATES_DIR.joinpath(file)
    return FileResponse(filename, media_type="application/octet-stream")
