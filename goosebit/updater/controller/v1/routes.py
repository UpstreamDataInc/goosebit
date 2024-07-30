import json
import logging

from fastapi import APIRouter, Depends
from fastapi.requests import Request

from goosebit.models import Firmware, UpdateStateEnum
from goosebit.settings import POLL_TIME_REGISTRATION
from goosebit.updater.manager import HandlingType, UpdateManager, get_update_manager
from goosebit.updates import generate_chunk

logger = logging.getLogger("DDI API")

router = APIRouter(prefix="/v1")


@router.get("/{dev_id}")
async def polling(
    request: Request,
    tenant: str,
    dev_id: str,
    updater: UpdateManager = Depends(get_update_manager),
):
    links = {}

    sleep = updater.poll_time
    device = await updater.get_device()

    if device.last_state == UpdateStateEnum.UNKNOWN:
        # device registration
        sleep = POLL_TIME_REGISTRATION
        links["configData"] = {
            "href": str(
                request.url_for(
                    "config_data",
                    tenant=tenant,
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
        handling_type, firmware = await updater.get_update()
        if handling_type != HandlingType.SKIP:
            links["deploymentBase"] = {
                "href": str(
                    request.url_for(
                        "deployment_base",
                        tenant=tenant,
                        dev_id=dev_id,
                        action_id=firmware.id,
                    )
                )
            }
            logger.info(f"Forced: update available, device={updater.dev_id}")

    return {
        "config": {"polling": {"sleep": sleep}},
        "_links": links,
    }


@router.put("/{dev_id}/configData")
async def config_data(
    request: Request,
    dev_id: str,
    tenant: str,
    updater: UpdateManager = Depends(get_update_manager),
):
    data = await request.json()
    # TODO: make standard schema to deal with this
    await updater.update_config_data(**data["data"])
    logger.info(f"Updating config data, device={updater.dev_id}")
    return {"success": True, "message": "Updated swupdate data."}


@router.get("/{dev_id}/deploymentBase/{action_id}")
async def deployment_base(
    request: Request,
    tenant: str,
    dev_id: str,
    action_id: int,
    updater: UpdateManager = Depends(get_update_manager),
):
    handling_type, firmware = await updater.get_update()

    logger.info(f"Request deployment base, device={updater.dev_id}")

    return {
        "id": f"{action_id}",
        "deployment": {
            "download": str(handling_type),
            "update": str(handling_type),
            "chunks": generate_chunk(request, firmware),
        },
    }


@router.post("/{dev_id}/deploymentBase/{action_id}/feedback")
async def deployment_feedback(
    request: Request,
    tenant: str,
    dev_id: str,
    action_id: int,
    updater: UpdateManager = Depends(get_update_manager),
):
    try:
        data = await request.json()
    except json.JSONDecodeError as e:
        logging.warning(
            f"Parsing deployment feedback failed, error={e}, device={dev_id}"
        )
        return
    try:
        execution = data["status"]["execution"]

        if execution == "proceeding":
            await updater.update_device_state(UpdateStateEnum.RUNNING)
            logger.debug(f"Installation in progress, device={updater.dev_id}")

        elif execution == "closed":
            state = data["status"]["result"]["finished"]

            await updater.update_force_update(False)
            await updater.update_log_complete(True)

            reported_firmware = await Firmware.get_or_none(id=data["id"])

            # From hawkBit docu: DDI defines also a status NONE which will not be interpreted by the update server
            # and handled like SUCCESS.
            if state == "success" or state == "none":
                await updater.update_device_state(UpdateStateEnum.FINISHED)

                # not guaranteed to be the correct rollout - see next comment.
                rollout = await updater.get_rollout()
                if rollout:
                    if rollout.firmware == reported_firmware:
                        rollout.success_count += 1
                        await rollout.save()
                    else:
                        logging.warning(
                            f"Updating rollout success stats failed, firmware={reported_firmware.id}, device={dev_id}"
                        )

                # setting the currently installed version based on the current assigned firmware / existing rollouts
                # is problematic. Better to assign custom action_id for each update (rollout id? firmware id? new id?).
                # Alternatively - but requires customization on the gateway side - use version reported by the gateway.
                await updater.update_fw_version(reported_firmware.version)
                logger.debug(
                    f"Installation successful, firmware={reported_firmware.version}, device={updater.dev_id}"
                )

            elif state == "failure":
                await updater.update_device_state(UpdateStateEnum.ERROR)

                # not guaranteed to be the correct rollout - see comment above.
                rollout = await updater.get_rollout()
                if rollout:
                    if rollout.firmware == reported_firmware:
                        rollout.failure_count += 1
                        await rollout.save()
                    else:
                        logging.warning(
                            f"Updating rollout failure stats failed, firmware={reported_firmware.id}, device={dev_id}"
                        )

                logger.debug(
                    f"Installation failed, firmware={reported_firmware.version}, device={updater.dev_id}"
                )

    except KeyError as e:
        logging.warning(
            f"Processing deployment feedback failed, error={e}, device={dev_id}"
        )

    try:
        log = data["status"]["details"]
        await updater.update_log("\n".join(log))
    except KeyError:
        logging.warning(f"No details to update update log, device={dev_id}")

    return {"id": str(action_id)}
