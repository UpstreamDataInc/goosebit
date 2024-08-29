from fastapi import APIRouter, HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse, RedirectResponse

from goosebit.db.models import Software

router = APIRouter(prefix="/download", tags=["download"])


@router.get("/{file_id}")
async def download_file(_: Request, file_id: int):
    software = await Software.get_or_none(id=file_id)
    if software is None:
        raise HTTPException(404)
    if software.local:
        return FileResponse(
            software.path,
            media_type="application/octet-stream",
            filename=software.path.name,
        )
    else:
        return RedirectResponse(url=software.uri)
