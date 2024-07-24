from fastapi import APIRouter, HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse

from goosebit.models import FirmwareUpdate
from goosebit.settings import UPDATES_DIR

router = APIRouter(prefix="/download")


@router.get("/by_name/{file}")
async def download_file_by_name(request: Request, file: str):
    filename = UPDATES_DIR.joinpath(file)
    return FileResponse(filename, media_type="application/octet-stream")


@router.get("/by_id/{file_id}")
async def download_file_by_id(request: Request, file_id: int):
    file = await FirmwareUpdate.get_or_none(id=file_id)
    if file is None:
        raise HTTPException(404)
    return FileResponse(file.path, media_type="application/octet-stream")
