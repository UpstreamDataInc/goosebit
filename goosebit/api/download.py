from fastapi import APIRouter, HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse, RedirectResponse

from goosebit.models import Firmware
from goosebit.settings import UPDATES_DIR

router = APIRouter(prefix="/download")


@router.get("/{file_id}")
async def download_file(request: Request, file_id: int):
    file = await Firmware.get_or_none(id=file_id)
    if file is None:
        raise HTTPException(404)
    if file.local:
        return FileResponse(
            file.path, media_type="application/octet-stream", filename=file.path.name
        )
    else:
        return RedirectResponse(url=file.uri)
