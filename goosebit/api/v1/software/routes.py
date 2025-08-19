from __future__ import annotations

import random
import string

from anyio import Path, open_file
from fastapi import APIRouter, File, Form, HTTPException, Security, UploadFile
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db.models import Rollout, Software
from goosebit.storage import storage
from goosebit.updates import create_software_update
from goosebit.util.path import validate_filename

from .requests import SoftwareDeleteRequest
from .responses import SoftwareResponse

router = APIRouter(prefix="/software", tags=["software"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["software"]["read"]()])],
)
async def software_get(_: Request) -> SoftwareResponse:
    software = await Software.all().prefetch_related("compatibility")
    return SoftwareResponse(software=software)


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["software"]["delete"]()])],
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

        if software.uri:
            try:
                await storage.delete_file(software.uri)
            except ValueError:
                pass

        await software.delete()
        success = True
    return StatusResponse(success=success)


@router.post(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["software"]["write"]()])],
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
    elif file is not None:
        # local file
        temp_dir = Path(storage.get_temp_dir())
        try:
            file_path = await validate_filename(file.filename, temp_dir)
        except ValueError as e:
            raise HTTPException(400, f"Invalid filename: {e}")
        tmp_file_path = temp_dir.joinpath("".join(random.choices(string.ascii_lowercase, k=12)) + ".tmp")
        file_absolute_path = await file_path.absolute()
        try:
            async with await open_file(tmp_file_path, "w+b") as f:
                await f.write(await file.read())
            software = await create_software_update(file_absolute_path.as_uri(), tmp_file_path)
        finally:
            await tmp_file_path.unlink(missing_ok=True)
    else:
        raise HTTPException(422)

    return {"id": software.id}
