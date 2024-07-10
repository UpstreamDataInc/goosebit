from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import FileResponse

from goosebit.settings import TOKEN_SWU_DIR, UPDATES_DIR
from goosebit.updater.manager import UpdateManager, get_update_manager

router = APIRouter(prefix="/v1")


@router.get("/{dev_id}/{file}")
async def download_file(request: Request, tenant: str, dev_id: str, file: str):
    filename = UPDATES_DIR.joinpath(file)
    return FileResponse(filename, media_type="application/octet-stream")


@router.get("/{dev_id}/cfd_conf/{file}")
async def download_cfd_conf(
    request: Request,
    tenant: str,
    dev_id: str,
    file: str,
    updater: UpdateManager = Depends(get_update_manager),
):
    filename = TOKEN_SWU_DIR.joinpath(dev_id, file)
    return FileResponse(filename, media_type="application/octet-stream")
