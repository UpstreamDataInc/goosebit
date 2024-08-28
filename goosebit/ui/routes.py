import aiofiles
from fastapi import APIRouter, Depends, Form, HTTPException, Security, UploadFile
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer

from goosebit.auth import redirect_if_unauthenticated, validate_user_permissions
from goosebit.models import Rollout, Software
from goosebit.settings import config
from goosebit.ui.nav import nav
from goosebit.updates import create_software_update

from . import bff
from .templates import templates

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter(prefix="/ui", dependencies=[Depends(redirect_if_unauthenticated)], include_in_schema=False)
router.include_router(bff.router)


@router.get("")
async def ui_root(request: Request):
    return RedirectResponse(request.url_for("home_ui"))


@router.get(
    "/home",
    dependencies=[Security(validate_user_permissions, scopes=["home.read"])],
)
@nav.route("Home", permissions=["home.read"])
async def home_ui(request: Request):
    return templates.TemplateResponse(request, "index.html.jinja", context={"title": "Home"})


@router.get(
    "/devices",
    dependencies=[Security(validate_user_permissions, scopes=["device.read"])],
)
@nav.route("Devices", permissions=["device.read"])
async def devices_ui(request: Request):
    return templates.TemplateResponse(request, "devices.html.jinja", context={"title": "Devices"})


@router.get(
    "/software",
    dependencies=[Security(validate_user_permissions, scopes=["software.read"])],
)
@nav.route("Software", permissions=["software.read"])
async def software_ui(request: Request):
    return templates.TemplateResponse(request, "software.html.jinja", context={"title": "Software"})


@router.post(
    "/upload/local",
    dependencies=[Security(validate_user_permissions, scopes=["software.write"])],
)
async def upload_update_local(
    request: Request,
    chunk: UploadFile = Form(...),
    init: bool = Form(...),
    done: bool = Form(...),
    filename: str = Form(...),
):
    file = config.artifacts_dir.joinpath(filename)
    config.artifacts_dir.mkdir(parents=True, exist_ok=True)

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


@router.post(
    "/upload/remote",
    dependencies=[Security(validate_user_permissions, scopes=["software.write"])],
)
async def upload_update_remote(request: Request, url: str = Form(...)):
    software = await Software.get_or_none(uri=url)
    if software is not None:
        rollout_count = await Rollout.filter(software=software).count()
        if rollout_count == 0:
            await software.delete()
        else:
            raise HTTPException(409, "Software with same URL already exists and is referenced by rollout")

    await create_software_update(url, None)


@router.get(
    "/rollouts",
    dependencies=[Security(validate_user_permissions, scopes=["rollout.read"])],
)
@nav.route("Rollouts", permissions=["rollout.read"])
async def rollouts_ui(request: Request):
    return templates.TemplateResponse(request, "rollouts.html.jinja", context={"title": "Rollouts"})


@router.get(
    "/logs/{dev_id}",
    dependencies=[Security(validate_user_permissions, scopes=["device.read"])],
)
async def logs_ui(request: Request, dev_id: str):
    return templates.TemplateResponse(request, "logs.html.jinja", context={"title": "Log", "device": dev_id})
