import time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request

from goosebit.device_manager import DeviceManager, get_device
from goosebit.settings import config
from goosebit.settings.schema import DeviceAuthMode

from ..db import Device
from . import controller


async def log_last_connection(request: Request, dev_id: str):
    device = await get_device(dev_id)
    if request.scope["config"].track_device_ip:
        await DeviceManager.update_last_connection(device, round(time.time()), request.client.host)
    else:
        await DeviceManager.update_last_connection(device, round(time.time()))


async def validate_device_token(request: Request, dev_id: str):
    if not request.scope["config"].device_auth.enable:
        return

    # parse device token, needs to be the `TargetToken`
    device_token = request.headers.get("Authorization")
    if device_token is not None:
        if device_token.startswith("TargetToken"):
            device_token = device_token.replace("TargetToken ", "")
        else:
            device_token = None

    device = await DeviceManager.get_device(dev_id)
    # setup mode should register devices and set up their auth token
    if request.scope["config"].device_auth.mode == DeviceAuthMode.SETUP:
        if device_token is None:
            return
        await DeviceManager.update_auth_token(device, device_token)

    # lax mode should register devices and check their token if they have one, but not register their tokens
    elif request.scope["config"].device_auth.mode == DeviceAuthMode.LAX:
        # should not be possible
        assert device is not None

        if not device.auth_token == device_token:
            raise HTTPException(401, "Device authentication token does not match.")

    # strict mode should ensure all device are already set up and have a token, then check the token
    elif request.scope["config"].device_auth.mode == DeviceAuthMode.STRICT:
        if device_token is None:
            raise HTTPException(401, "Device authentication token is required in strict mode.")
        # do not create a device in strict mode
        device = await Device.get_or_none(id=dev_id)
        if device is None:
            raise HTTPException(401, "Cannot register a new device in strict mode.")
        if not device.auth_token == device_token:
            raise HTTPException(401, "Device authentication token does not match.")
    elif request.scope["config"].device_auth.mode == DeviceAuthMode.STRICT_EXTERNAL:
        if device_token is None:
            raise HTTPException(401, "Device authentication token is required in strict mode.")
        # do not create a device in strict mode
        device = await Device.get_or_none(id=dev_id)
        if device is None:
            raise HTTPException(401, "Cannot register a new device in strict mode.")
        external_request_data = {"device_id": dev_id, "secret": device_token}
        # Make request to an external service to validate the token
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    request.scope["config"].device_auth.external_uri, json=external_request_data, timeout=5.0
                )
                response.raise_for_status()
                validation_result = response.json()

                if not validation_result.get("valid", False):
                    raise HTTPException(401, validation_result.get("message", "Token validation failed"))
        except httpx.HTTPError as e:
            raise HTTPException(500, f"Error communicating with authentication service: {str(e)}")


router = APIRouter(
    prefix=f"/{config.tenant}",
    dependencies=[Depends(log_last_connection), Depends(validate_device_token)],
    tags=["ddi"],
)
router.include_router(controller.router)
