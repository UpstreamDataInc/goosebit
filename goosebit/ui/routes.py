import aiofiles
from fastapi import APIRouter, Depends, Form, HTTPException, Security, UploadFile
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer

from goosebit.auth import authenticate_session, validate_user_permissions
from goosebit.models import Firmware, Rollout
from goosebit.permissions import Permissions
from goosebit.settings import config
from goosebit.ui.nav import nav
from goosebit.ui.templates import templates
from goosebit.updates import create_firmware_update

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter(prefix="/ui", dependencies=[Depends(authenticate_session)], include_in_schema=False)


@router.get("/")
async def ui_root(request: Request):
    return RedirectResponse(request.url_for("home_ui"))


@router.get(
    "/home",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.HOME.READ])],
)
@nav.route("Home", permissions=Permissions.HOME.READ)
async def home_ui(request: Request):
    return templates.TemplateResponse(request, "index.html", context={"title": "Home"})


@router.get(
    "/firmware",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])],
)
@nav.route("Firmware", permissions=Permissions.FIRMWARE.READ)
async def firmware_ui(request: Request):
    return templates.TemplateResponse(request, "firmware.html", context={"title": "Firmware"})


@router.post(
    "/upload/local",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.WRITE])],
)
async def upload_update_local(
    request: Request,
    chunk: UploadFile = Form(...),
    init: bool = Form(...),
    done: bool = Form(...),
    filename: str = Form(...),
):
    file = config.artifacts_dir.joinpath(filename)

    temp_file = file.with_suffix(".tmp")
    if init:
        temp_file.unlink(missing_ok=True)

    contents = await chunk.read()

    async with aiofiles.open(temp_file, mode="ab") as f:
        await f.write(contents)

    if done:
        try:
            await create_firmware_update(file.absolute().as_uri(), temp_file)
        finally:
            temp_file.unlink(missing_ok=True)


@router.post(
    "/upload/remote",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.WRITE])],
)
async def upload_update_remote(request: Request, url: str = Form(...)):
    firmware = await Firmware.get_or_none(uri=url)
    if firmware is not None:
        rollout_count = await Rollout.filter(firmware=firmware).count()
        if rollout_count == 0:
            await firmware.delete()
        else:
            raise HTTPException(409, "Firmware with same URL already exists and is referenced by rollout")

    await create_firmware_update(url, None)


@router.get(
    "/devices",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.DEVICE.READ])],
)
@nav.route("Devices", permissions=Permissions.DEVICE.READ)
async def devices_ui(request: Request):
    return templates.TemplateResponse(request, "devices.html", context={"title": "Devices"})


@router.get(
    "/rollouts",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.READ])],
)
@nav.route("Rollouts", permissions=Permissions.ROLLOUT.READ)
async def rollouts_ui(request: Request):
    return templates.TemplateResponse(request, "rollouts.html", context={"title": "Rollouts"})


@router.get(
    "/logs/{dev_id}",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.DEVICE.READ])],
)
async def logs_ui(request: Request, dev_id: str):
    return templates.TemplateResponse(request, "logs.html", context={"title": "Log", "device": dev_id})
