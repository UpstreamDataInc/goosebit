from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import FileResponse

from goosebit.settings import UPDATES_DIR

router = APIRouter(prefix="/v1")


@router.get("/{dev_id}/{file}")
async def download_file(request: Request, tenant: str, dev_id: str, file: str):
    filename = UPDATES_DIR.joinpath(file)
    return FileResponse(filename, media_type="application/octet-stream")
