import time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request

from goosebit.device_manager import DeviceManager, get_device_or_none
from goosebit.settings import config
from goosebit.settings.schema import DeviceAuthMode, ExternalAuthMode

from ..db import Device
from . import controller


async def log_last_connection(request: Request, dev_id: str):
    device = await get_device_or_none(dev_id)

    if not device:
        return

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

    # setup mode should register devices and set up their auth token
    if request.scope["config"].device_auth.mode == DeviceAuthMode.SETUP:
        device = await DeviceManager.get_device(dev_id)
        if device_token is None:
            return
        await DeviceManager.update_auth_token(device, device_token)

    # lax mode should register devices and check their token if they have one, but not register their tokens
    elif request.scope["config"].device_auth.mode == DeviceAuthMode.LAX:
        device = await DeviceManager.get_device(dev_id)
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

    # external mode should check the token with an external service
    elif request.scope["config"].device_auth.mode == DeviceAuthMode.EXTERNAL:
        if device_token is None:
            raise HTTPException(401, "Device authentication token is required in external mode.")

        try:
            async with httpx.AsyncClient() as client:
                if request.scope["config"].device_auth.external_mode == ExternalAuthMode.BEARER:
                    response = await client.post(
                        request.scope["config"].device_auth.external_url,
                        headers={"Authorization": f"Bearer {device_token}"},
                    )
                elif request.scope["config"].device_auth.external_mode == ExternalAuthMode.JSON:
                    json = {request.scope["config"].device_auth.external_json_key: device_token}
                    response = await client.post(
                        request.scope["config"].device_auth.external_url,
                        json=json,
                    )

                if response.status_code != 200:
                    raise HTTPException(401, "Device authentication token is invalid.")
                else:
                    await DeviceManager.get_device(dev_id)
        except httpx.RequestError as e:
            raise HTTPException(401, f"Error communicating with authentication service: {str(e)}")
        except Exception as e:
            raise HTTPException(401, f"Error: {str(e)}")


router = APIRouter(
    prefix=f"/{config.tenant}",
    dependencies=[Depends(log_last_connection), Depends(validate_device_token)],
    tags=["ddi"],
)
router.include_router(controller.router)
