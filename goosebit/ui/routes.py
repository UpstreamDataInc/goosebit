import aiofiles
from fastapi import APIRouter, Depends, Form, HTTPException, Security, UploadFile
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer

from goosebit.auth import authenticate_session, validate_user_permissions
from goosebit.permissions import Permissions
from goosebit.settings import UPDATES_DIR
from goosebit.ui.templates import templates
from goosebit.updater.misc import validate_filename

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter(
    prefix="/ui", dependencies=[Depends(authenticate_session)], include_in_schema=False
)


@router.get("/")
async def ui_root(request: Request):
    return RedirectResponse(request.url_for("home_ui"))


@router.get(
    "/firmware",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])
    ],
)
async def firmware_ui(request: Request):
    return templates.TemplateResponse(
        "firmware.html", context={"request": request, "title": "Firmware"}
    )


@router.post(
    "/upload",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.WRITE])
    ],
)
async def upload_update(
    request: Request,
    chunk: UploadFile = Form(...),
    init: bool = Form(...),
    done: bool = Form(...),
    filename: str = Form(...),
):
    if not validate_filename(filename):
        raise HTTPException(400, detail="Could not parse file data, invalid filename.")

    file = UPDATES_DIR.joinpath(filename)
    tmpfile = file.with_suffix(".tmp")
    contents = await chunk.read()
    if init:
        file.unlink(missing_ok=True)

    async with aiofiles.open(tmpfile, mode="ab") as f:
        await f.write(contents)
    if done:
        tmpfile.replace(file)


@router.get(
    "/home",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.HOME.READ])],
)
async def home_ui(request: Request):
    return templates.TemplateResponse(
        "index.html", context={"request": request, "title": "Home"}
    )


@router.get(
    "/devices",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.DEVICE.READ])
    ],
)
async def devices_ui(request: Request):
    return templates.TemplateResponse(
        "devices.html", context={"request": request, "title": "Devices"}
    )


@router.get(
    "/rollouts",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.READ])
    ],
)
async def rollouts_ui(request: Request):
    return templates.TemplateResponse(
        "rollouts.html", context={"request": request, "title": "Rollouts"}
    )


@router.get(
    "/logs/{dev_id}",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.DEVICE.READ])
    ],
)
async def logs_ui(request: Request, dev_id: str):
    return templates.TemplateResponse(
        "logs.html", context={"request": request, "title": "Log", "device": dev_id}
    )
