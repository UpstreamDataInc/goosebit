from pathlib import Path

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, Security, UploadFile
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.db.models import Rollout, Software
from goosebit.settings import config
from goosebit.updates import create_software_update

from .requests import SoftwareDeleteRequest
from .responses import SoftwareResponse

router = APIRouter(prefix="/software", tags=["software"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["software.read"])],
)
async def software_get(_: Request) -> SoftwareResponse:
    return await SoftwareResponse.convert(await Software.all().prefetch_related("compatibility"))


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["software.delete"])],
)
async def software_delete(_: Request, delete_req: SoftwareDeleteRequest) -> StatusResponse:
    success = False
    for software_id in delete_req.software_ids:
        software = await Software.get_or_none(id=software_id)

        if software is None:
            continue

        rollout_count = await Rollout.filter(software=software).count()
        if rollout_count > 0:
            raise HTTPException(409, "Software is referenced by rollout")

        if software.local:
            path = software.path
            if path.exists():
                path.unlink()

        await software.delete()
        success = True
    return StatusResponse(success=success)


@router.post(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["software.write"])],
)
async def post_update(_: Request, file: UploadFile | None = File(None), url: str | None = Form(None)):
    if url is not None:
        # remote file
        software = await Software.get_or_none(uri=url)
        if software is not None:
            rollout_count = await Rollout.filter(software=software).count()
            if rollout_count == 0:
                await software.delete()
            else:
                raise HTTPException(409, "Software with same URL already exists and is referenced by rollout")

        software = await create_software_update(url, None)
    else:
        # local file
        file_path = config.artifacts_dir.joinpath(file.filename)

        async with aiofiles.tempfile.NamedTemporaryFile("w+b") as f:
            await f.write(await file.read())
            software = await create_software_update(file_path.absolute().as_uri(), Path(f.name))

    return {"id": software.id}
