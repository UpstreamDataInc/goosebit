from fastapi import APIRouter, HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse, RedirectResponse

from goosebit.models import FirmwareUpdate
from goosebit.settings import UPDATES_DIR

router = APIRouter(prefix="/download")


@router.get("/by_name/{filename}")
async def download_file_by_name(request: Request, filename: str):
    file = UPDATES_DIR.joinpath(filename)
    return FileResponse(
        file, media_type="application/octet-stream", filename=file.path.name
    )


@router.get("/by_id/{file_id}")
async def download_file_by_id(request: Request, file_id: int):
    file = await FirmwareUpdate.get_or_none(id=file_id)
    if file is None:
        raise HTTPException(404)
    if file.local:
        return FileResponse(
            file.path, media_type="application/octet-stream", filename=file.path.name
        )
    else:
        return RedirectResponse(url=file.uri)
