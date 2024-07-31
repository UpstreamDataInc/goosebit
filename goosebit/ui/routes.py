import aiofiles
from fastapi import APIRouter, Depends, Form, Security, UploadFile
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer

from goosebit.auth import authenticate_session, validate_user_permissions
from goosebit.models import Firmware
from goosebit.permissions import Permissions
from goosebit.settings import UPDATES_DIR
from goosebit.ui.templates import templates
from goosebit.updates import create_firmware_update

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter(prefix="/ui", dependencies=[Depends(authenticate_session)], include_in_schema=False)


@router.get("/")
async def ui_root(request: Request):
    return RedirectResponse(request.url_for("home_ui"))


@router.get(
    "/firmware",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])],
)
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
    file = UPDATES_DIR.joinpath(filename)
    firmware = await Firmware.get_or_none(uri=file.absolute().as_uri())
    if firmware is not None:
        await firmware.delete()

    tmpfile = file.with_suffix(".tmp")
    contents = await chunk.read()
    if init:
        file.unlink(missing_ok=True)

    async with aiofiles.open(tmpfile, mode="ab") as f:
        await f.write(contents)
    if done:
        tmpfile.replace(file)
        await create_firmware_update(file.absolute().as_uri())


@router.post(
    "/upload/remote",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.WRITE])],
)
async def upload_update_remote(request: Request, url: str = Form(...)):
    firmware = await Firmware.get_or_none(uri=url)
    if firmware is not None:
        await firmware.delete()

    await create_firmware_update(url)


@router.get(
    "/home",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.HOME.READ])],
)
async def home_ui(request: Request):
    return templates.TemplateResponse(request, "index.html", context={"title": "Home"})


@router.get(
    "/devices",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.DEVICE.READ])],
)
async def devices_ui(request: Request):
    return templates.TemplateResponse(request, "devices.html", context={"title": "Devices"})


@router.get(
    "/rollouts",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.READ])],
)
async def rollouts_ui(request: Request):
    return templates.TemplateResponse(request, "rollouts.html", context={"title": "Rollouts"})


@router.get(
    "/logs/{dev_id}",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.DEVICE.READ])],
)
async def logs_ui(request: Request, dev_id: str):
    return templates.TemplateResponse(request, "logs.html", context={"title": "Log", "device": dev_id})
