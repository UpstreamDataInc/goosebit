from __future__ import annotations

import aiofiles
from fastapi import APIRouter, Security, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.params import Form
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.auth import validate_user_permissions
from goosebit.db.models import Software
from goosebit.ui.bff.software.responses import BFFSoftwareResponse
from goosebit.models import Rollout, Software
from goosebit.settings import config
from goosebit.updates import create_software_update

from ..responses import StatusResponse
from .requests import SoftwareDeleteRequest
from .responses import BFFSoftwareResponse

router = APIRouter(prefix="/software")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["software.read"])],
)
async def software_get(request: Request) -> BFFSoftwareResponse:
    def search_filter(search_value):
        return Q(uri__icontains=search_value) | Q(version__icontains=search_value)

    query = Software.all().prefetch_related("compatibility")
    total_records = await Software.all().count()

    return await BFFSoftwareResponse.convert(request, query, search_filter, total_records)


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["software.delete"])],
)
async def software_delete(_: Request, files: SoftwareDeleteRequest) -> StatusResponse:
    success = False
    for f_id in files.files:
        software = await Software.get_or_none(id=f_id)

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
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.SOFTWARE.WRITE])],
)
async def post_update(
    request: Request,
    url: str = Form(default=None),
    chunk: UploadFile = Form(default=None),
    init: bool = Form(default=None),
    done: bool = Form(default=None),
    filename: str = Form(default=None),
):
    if url is not None:
        # remote file
        software = await Software.get_or_none(uri=url)
        if software is not None:
            rollout_count = await Rollout.filter(software=software).count()
            if rollout_count == 0:
                await software.delete()
            else:
                raise HTTPException(409, "Software with same URL already exists and is referenced by rollout")

        await create_software_update(url, None)
    else:
        # local file
        file = config.artifacts_dir.joinpath(filename)

        temp_file = file.with_suffix(".tmp")
        if init:
            temp_file.unlink(missing_ok=True)

        contents = await chunk.read()

        async with aiofiles.open(temp_file, mode="ab") as f:
            await f.write(contents)

        if done:
            try:
                await create_software_update(file.absolute().as_uri(), temp_file)
            finally:
                temp_file.unlink(missing_ok=True)
