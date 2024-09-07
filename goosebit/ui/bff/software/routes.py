from __future__ import annotations

from anyio import Path, open_file
from fastapi import APIRouter, Form, HTTPException, Security, UploadFile
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.api.v1.software import routes
from goosebit.auth import validate_user_permissions
from goosebit.db.models import Rollout, Software
from goosebit.settings import config
from goosebit.updates import create_software_update

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


router.add_api_route(
    "",
    routes.software_delete,
    methods=["DELETE"],
    dependencies=[Security(validate_user_permissions, scopes=["software.delete"])],
    name="bff_software_delete",
)


@router.post(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["software.write"])],
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
        artifacts_dir = Path(config.artifacts_dir)
        file = artifacts_dir.joinpath(filename)
        await artifacts_dir.mkdir(parents=True, exist_ok=True)

        temp_file = file.with_suffix(".tmp")
        if init:
            await temp_file.unlink(missing_ok=True)

        async with await open_file(temp_file, "ab") as f:
            await f.write(await chunk.read())

        if done:
            try:
                absolute = await file.absolute()
                await create_software_update(absolute.as_uri(), temp_file)
            finally:
                await temp_file.unlink(missing_ok=True)
