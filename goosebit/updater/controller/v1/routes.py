import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse, RedirectResponse, Response

from goosebit.db.models import Software, UpdateStateEnum
from goosebit.settings import config
from goosebit.updater.manager import HandlingType, UpdateManager, get_update_manager
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
async def polling(request: Request, dev_id: str, updater: UpdateManager = Depends(get_update_manager)):
    links = {}

    sleep = updater.poll_time
    device = await updater.get_device()

    if device.last_state == UpdateStateEnum.UNKNOWN:
        # device registration
        sleep = config.poll_time_registration
        links["configData"] = {
            "href": str(
                request.url_for(
                    "config_data",
                    dev_id=dev_id,
                )
            )
        }
        logger.info(f"Skip: registration required, device={updater.dev_id}")

    elif device.last_state == UpdateStateEnum.ERROR and not device.force_update:
        logger.warning(f"Skip: device in error state, device={updater.dev_id}")
        pass

    else:
        # provide update if available. Note: this is also required while in state "running", otherwise swupdate
        # won't confirm a successful testing (might be a bug/problem in swupdate)
        handling_type, software = await updater.get_update()
        if handling_type != HandlingType.SKIP:
            links["deploymentBase"] = {
                "href": str(
                    request.url_for(
                        "deployment_base",
                        dev_id=dev_id,
                        action_id=software.id,
                    )
                )
            }
            logger.info(f"Forced: update available, device={updater.dev_id}")

    return {
        "config": {"polling": {"sleep": sleep}},
        "_links": links,
    }


@router.put("/{dev_id}/configData")
async def config_data(_: Request, cfg: ConfigDataSchema, updater: UpdateManager = Depends(get_update_manager)):
    await updater.update_config_data(**cfg.data)
    logger.info(f"Updating config data, device={updater.dev_id}")
    return {"success": True, "message": "Updated swupdate data."}


@router.get("/{dev_id}/deploymentBase/{action_id}")
async def deployment_base(
    request: Request,
    action_id: int,
    updater: UpdateManager = Depends(get_update_manager),
):
    handling_type, software = await updater.get_update()

    logger.info(f"Request deployment base, device={updater.dev_id}")

    return {
        "id": str(action_id),
        "deployment": {
            "download": str(handling_type),
            "update": str(handling_type),
            "chunks": await generate_chunk(request, updater),
        },
    }


@router.post("/{dev_id}/deploymentBase/{action_id}/feedback")
async def deployment_feedback(
    _: Request, data: FeedbackSchema, action_id: int, updater: UpdateManager = Depends(get_update_manager)
):
    if data.status.execution == FeedbackStatusExecutionState.PROCEEDING:
        await updater.update_device_state(UpdateStateEnum.RUNNING)
        logger.debug(f"Installation in progress, device={updater.dev_id}")

    elif data.status.execution == FeedbackStatusExecutionState.CLOSED:
        await updater.update_force_update(False)
        await updater.update_log_complete(True)

        reported_software = await Software.get_or_none(id=action_id)

        # From hawkBit docu: DDI defines also a status NONE which will not be interpreted by the update server
        # and handled like SUCCESS.
        if data.status.result.finished in [FeedbackStatusResultFinished.SUCCESS, FeedbackStatusResultFinished.NONE]:
            await updater.update_device_state(UpdateStateEnum.FINISHED)

            # not guaranteed to be the correct rollout - see next comment.
            rollout = await updater.get_rollout()
            if rollout:
                if rollout.software == reported_software:
                    rollout.success_count += 1
                    await rollout.save()
                else:
                    logging.warning(
                        f"Updating rollout success stats failed, software={reported_software.id}, device={updater.dev_id}"  # noqa: E501
                    )

            # setting the currently installed version based on the current assigned software / existing rollouts
            # is problematic. Better to assign custom action_id for each update (rollout id? software id? new id?).
            # Alternatively - but requires customization on the gateway side - use version reported by the gateway.
            await updater.update_sw_version(reported_software.version)
            logger.debug(f"Installation successful, software={reported_software.version}, device={updater.dev_id}")

        elif data.status.result.finished == FeedbackStatusResultFinished.FAILURE:
            await updater.update_device_state(UpdateStateEnum.ERROR)

            # not guaranteed to be the correct rollout - see comment above.
            rollout = await updater.get_rollout()
            if rollout:
                if rollout.software == reported_software:
                    rollout.failure_count += 1
                    await rollout.save()
                else:
                    logging.warning(
                        f"Updating rollout failure stats failed, software={reported_software.id}, device={updater.dev_id}"  # noqa: E501
                    )

            logger.debug(f"Installation failed, software={reported_software.version}, device={updater.dev_id}")
    else:
        logging.warning(
            f"Device reported unhandled execution state, state={data.status.execution}, device={updater.dev_id}"
        )

    try:
        log = data.status.details
        await updater.update_log("\n".join(log))
    except AttributeError:
        logging.warning(f"No details to update device update log, device={updater.dev_id}")

    return {"id": str(action_id)}


@router.head("/{dev_id}/download")
async def download_artifact_head(_: Request, updater: UpdateManager = Depends(get_update_manager)):
    _, software = await updater.get_update()
    if software is None:
        raise HTTPException(404)

    response = Response()
    response.headers["Content-Length"] = str(software.size)
    return response


@router.get("/{dev_id}/download")
async def download_artifact(_: Request, updater: UpdateManager = Depends(get_update_manager)):
    _, software = await updater.get_update()
    if software is None:
        raise HTTPException(404)
    if software.local:
        return FileResponse(
            software.path,
            media_type="application/octet-stream",
            filename=software.path.name,
        )
    else:
        return RedirectResponse(url=software.uri)
