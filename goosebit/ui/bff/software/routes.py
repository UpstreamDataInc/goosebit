from __future__ import annotations

from typing import Annotated

from anyio import Path, open_file
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Security, UploadFile
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.api.v1.software import routes
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db.models import Hardware, Rollout, Software
from goosebit.storage import storage
from goosebit.ui.bff.common.requests import DataTableRequest
from goosebit.ui.bff.common.util import parse_datatables_query
from goosebit.updates import create_software_update
from goosebit.util.path import validate_filename

from ..common.columns import SoftwareColumns
from ..common.responses import DTColumns
from .responses import BFFSoftwareResponse

router = APIRouter(prefix="/software")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["software"]["read"]()])],
)
async def software_get(
    dt_query: Annotated[DataTableRequest, Depends(parse_datatables_query)],
    ids: list[str] = Query(default=None),
) -> BFFSoftwareResponse:
    filters: list[Q] = []

    def search_filter(search_value):
        base_filter = Q(Q(uri__icontains=search_value), Q(version__icontains=search_value), join_type="OR")
        return Q(base_filter, *filters, join_type="AND")

    query = Software.all().prefetch_related("compatibility")

    if ids:
        hardware = await Hardware.filter(devices__id__in=ids).distinct()
        filters.append(Q(*[Q(compatibility__id=c.id) for c in hardware], join_type="AND"))

    return await BFFSoftwareResponse.convert(dt_query, query, search_filter, Q(*filters))


router.add_api_route(
    "",
    routes.software_delete,
    methods=["DELETE"],
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["software"]["delete"]()])],
    name="bff_software_delete",
)


@router.post(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["software"]["write"]()])],
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
        temp_dir = Path(storage.get_temp_dir())

        try:
            file_path = await validate_filename(filename, temp_dir)
        except ValueError as e:
            raise HTTPException(400, f"Invalid filename: {e}")

        temp_file = file_path.with_suffix(".tmp")
        if init:
            await temp_file.unlink(missing_ok=True)

        async with await open_file(temp_file, "ab") as f:
            await f.write(await chunk.read())

        if done:
            try:
                absolute = await file_path.absolute()
                await create_software_update(absolute.as_uri(), temp_file)
            finally:
                await temp_file.unlink(missing_ok=True)


@router.get(
    "/columns",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["software"]["read"]()])],
    response_model_exclude_none=True,
)
async def devices_get_columns() -> DTColumns:
    columns = list(
        filter(
            None,
            [
                SoftwareColumns.id,
                SoftwareColumns.name,
                SoftwareColumns.version,
                SoftwareColumns.compatibility,
                SoftwareColumns.size,
            ],
        )
    )
    return DTColumns(columns=columns)
