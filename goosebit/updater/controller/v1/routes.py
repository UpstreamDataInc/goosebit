import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from fastapi.responses import (
    FileResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)

from goosebit.db.models import Device, Software, UpdateStateEnum
from goosebit.device_manager import DeviceManager, HandlingType, get_device
from goosebit.settings import config
from goosebit.storage import storage
from goosebit.updates import generate_chunk

from .schema import (
    ConfigDataSchema,
    FeedbackSchema,
    FeedbackStatusExecutionState,
    FeedbackStatusResultFinished,
)

logger = logging.getLogger("DDI API")

router = APIRouter(prefix="/v1")


@router.get("/{dev_id}")
async def polling(request: Request, device: Device = Depends(get_device)):
    links: dict[str, dict[str, str]] = {}

    if device is None:
        raise HTTPException(404)

    sleep = config.poll_time

    if device.last_state == UpdateStateEnum.UNKNOWN:
        # device registration: force device to poll again in 10s. After registration, an update might be available
        sleep = "00:00:10"
        links["configData"] = {
            "href": str(
                request.url_for(
                    "config_data",
                    dev_id=device.id,
                )
            )
        }
        logger.info(f"Skip: registration required, device={device.id}")

    elif device.last_state == UpdateStateEnum.ERROR and not device.force_update:
        logger.info(f"Skip: device in error state, device={device.id}")

    else:
        # provide update if available. Note: this is also required while in state "running", otherwise swupdate
        # won't confirm a successful testing (might be a bug/problem in swupdate)
        handling_type, software = await DeviceManager.get_update(device)
        if handling_type != HandlingType.SKIP and software is not None:
            number_of_running = await Device.filter(last_state=UpdateStateEnum.RUNNING).count()
            if number_of_running < config.max_concurrent_updates or device.last_state == UpdateStateEnum.RUNNING:
                links["deploymentBase"] = {
                    "href": str(
                        request.url_for(
                            "deployment_base",
                            dev_id=device.id,
                            action_id=software.id,
                        )
                    )
                }
                logger.info(f"Forced: update available, device={device.id}")
        else:
            number_of_running = await Device.filter(last_state=UpdateStateEnum.RUNNING).count()
            if number_of_running < config.max_concurrent_updates or device.last_state == UpdateStateEnum.RUNNING:
                plugin_sources = await DeviceManager.get_alt_src_updates(request, device)
                for handling_type, _ in plugin_sources:
                    if handling_type == HandlingType.SKIP:
                        continue
                    links["deploymentBase"] = {
                        "href": str(
                            request.url_for(
                                "deployment_base",
                                dev_id=device.id,
                                action_id=-1,  # custom plugin
                            )
                        )
                    }
                    break
    return {
        "config": {"polling": {"sleep": sleep}},
        "_links": links,
    }


@router.put("/{dev_id}/configData")
async def config_data(_: Request, cfg: ConfigDataSchema, device: Device = Depends(get_device)):
    await DeviceManager.update_config_data(device, **cfg.data)
    logger.info(f"Updating config data, device={device.id}")
    return {"success": True, "message": "Updated swupdate data."}


@router.get("/{dev_id}/deploymentBase/{action_id}")
async def deployment_base(
    request: Request,
    action_id: int,
    device: Device = Depends(get_device),
):
    handling_type, software = await DeviceManager.get_update(device)

    logger.info(f"Request deployment base, device={device.id}")
    if not handling_type == HandlingType.SKIP:
        return {
            "id": str(action_id),
            "deployment": {
                "download": str(handling_type),
                "update": str(handling_type),
                "chunks": [chunk.model_dump(by_alias=True) for chunk in (await generate_chunk(request, device))],
            },
        }
    else:
        plugin_sources = await DeviceManager.get_alt_src_updates(request, device)
        for handling_type, chunk in plugin_sources:
            if handling_type == HandlingType.SKIP or chunk is None:
                continue
            return {
                "id": str(action_id),
                "deployment": {
                    "download": str(handling_type),
                    "update": str(handling_type),
                    "chunks": [chunk.model_dump(by_alias=True)],
                },
            }


@router.post("/{dev_id}/deploymentBase/{action_id}/feedback")
async def deployment_feedback(_: Request, data: FeedbackSchema, action_id: int, device: Device = Depends(get_device)):
    if data.status.execution == FeedbackStatusExecutionState.PROCEEDING:
        if device and device.last_state != UpdateStateEnum.RUNNING:
            await DeviceManager.deployment_action_start(device)
            await DeviceManager.update_device_state(device, UpdateStateEnum.RUNNING)

        logger.debug(f"Installation in progress, device={device.id}")

    elif data.status.execution == FeedbackStatusExecutionState.CLOSED:
        await DeviceManager.update_force_update(device, False)

        reported_software = await Software.get_or_none(id=action_id)

        # From hawkBit docu: DDI defines also a status NONE which will not be interpreted by the update server
        # and handled like SUCCESS.
        if data.status.result.finished in [FeedbackStatusResultFinished.SUCCESS, FeedbackStatusResultFinished.NONE]:
            await DeviceManager.deployment_action_success(device)
            await DeviceManager.update_device_state(device, UpdateStateEnum.FINISHED)

            rollout = await DeviceManager.get_rollout(device)
            if rollout:
                if rollout.software == reported_software:
                    rollout.success_count += 1
                    await rollout.save()
                else:
                    # edge case where device update mode got changed while update was running
                    logging.warning(
                        f"Updating rollout success stats failed, action_id={action_id}, device={device.id}"
                        # noqa: E501
                    )

            if reported_software:
                await DeviceManager.update_sw_version(device, reported_software.version)

            software_version = reported_software.version if reported_software else None
            logger.debug(f"Installation successful, software={software_version}, device={device.id}")

        elif data.status.result.finished == FeedbackStatusResultFinished.FAILURE:
            await DeviceManager.update_device_state(device, UpdateStateEnum.ERROR)

            rollout = await DeviceManager.get_rollout(device)
            if rollout:
                if rollout.software == reported_software:
                    rollout.failure_count += 1
                    await rollout.save()
                else:
                    # edge case where device update mode got changed while update was running
                    logging.warning(
                        f"Updating rollout failure stats failed, action_id={action_id}, device={device.id}"
                        # noqa: E501
                    )

            software_version = reported_software.version if reported_software else None
            logger.debug(f"Installation failed, software={software_version}, device={device.id}")
    else:
        logging.error(f"Device reported unhandled execution state, state={data.status.execution}, device={device.id}")

    try:
        log = data.status.details
        if log is not None:
            await DeviceManager.update_log(device, "\n".join(log))
    except AttributeError:
        logging.warning(f"No details to update device update log, device={device.id}")

    return {"id": str(action_id)}


@router.head("/{dev_id}/download")
async def download_artifact_head(_: Request, device: Device = Depends(get_device)):
    _, software = await DeviceManager.get_update(device)
    if software is None:
        raise HTTPException(404)

    response = Response()
    response.headers["Content-Length"] = str(software.size)
    return response


@router.get("/{dev_id}/download")
async def download_artifact(_: Request, device: Device = Depends(get_device)):
    _, software = await DeviceManager.get_update(device)
    if software is None:
        raise HTTPException(404)

    if software.local:
        return FileResponse(
            software.path,
            media_type="application/octet-stream",
            filename=software.path.name,
        )

    try:
        url = await storage.get_download_url(software.uri)
        return RedirectResponse(url=url)
    except ValueError:
        # Fallback to streaming if redirect fails.
        file_stream = storage.get_file_stream(software.uri)
        return StreamingResponse(
            file_stream,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={software.path.name}"},
        )
