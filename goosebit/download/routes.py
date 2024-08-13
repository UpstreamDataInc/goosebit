from fastapi import APIRouter, HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse, RedirectResponse
from starlette.responses import Response

from goosebit.models import Firmware

router = APIRouter(prefix="/download")


@router.head("/{file_id}")
async def download_file_head(_: Request, file_id: int):
    firmware = await Firmware.get_or_none(id=file_id)
    if firmware is None:
        raise HTTPException(404)

    response = Response()
    response.headers["Content-Length"] = str(firmware.size)
    return response


@router.get("/{file_id}")
async def download_file(_: Request, file_id: int):
    firmware = await Firmware.get_or_none(id=file_id)
    if firmware is None:
        raise HTTPException(404)
    if firmware.local:
        return FileResponse(
            firmware.path,
            media_type="application/octet-stream",
            filename=firmware.path.name,
        )
    else:
        return RedirectResponse(url=firmware.uri)
