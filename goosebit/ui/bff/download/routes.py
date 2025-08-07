from fastapi import APIRouter, HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse

from goosebit.db.models import Software
from goosebit.storage import storage

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

    try:
        url = await storage.get_download_url(software.uri)
        return RedirectResponse(url=url)
    except Exception:
        # Fallback to streaming if redirect fails.
        file_stream = storage.get_file_stream(software.uri)
        return StreamingResponse(
            file_stream,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={software.path.name}"},
        )
