import json

from fastapi import APIRouter, Depends
from fastapi.requests import Request

from goosebit.settings import POLL_TIME_REGISTRATION
from goosebit.updater.manager import UpdateManager, get_update_manager

# v1 is hardware revision
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
    last_state = updater.device.last_state

    if last_state == "unknown":
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

    elif last_state == "error" and not updater.force_update:
        # nothing to do
        pass

    else:
        # provide update if available. Note: this is also required while in state "running", otherwise swupdate
        # won't confirm a successful testing (might be a bug/problem in swupdate)
        update = await updater.get_update_mode()
        if update != "skip":
            links["deploymentBase"] = {
                "href": str(
                    request.url_for(
                        "deployment_base",
                        tenant=tenant,
                        dev_id=dev_id,
                        action_id=1,
                    )
                )
            }

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
    return {"success": True, "message": "Updated swupdate data."}


@router.get("/{dev_id}/deploymentBase/{action_id}")
async def deployment_base(
    request: Request,
    tenant: str,
    dev_id: str,
    action_id: int,
    updater: UpdateManager = Depends(get_update_manager),
):
    artifact = await updater.get_update_file()
    update = await updater.get_update_mode()
    await updater.save()

    return {
        "id": f"{action_id}",
        "deployment": {
            "download": update,
            "update": update,
            "chunks": artifact.generate_chunk(request, tenant=tenant, dev_id=dev_id),
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
    except json.JSONDecodeError:
        return
    try:
        execution = data["status"]["execution"]

        if execution == "proceeding":
            await updater.update_device_state("running")

        elif execution == "closed":
            state = data["status"]["result"]["finished"]

            updater.force_update = False
            updater.update_complete = True

            # From hawkBit docu: DDI defines also a status NONE which will not be interpreted by the update server
            # and handled like SUCCESS.
            if state == "success" or state == "none":
                await updater.update_device_state("finished")

                # not guaranteed to be the correct rollout - see next comment.
                rollout = await updater.get_rollout()
                if rollout:
                    file = rollout.fw_file
                    rollout.success_count += 1
                    await rollout.save()
                else:
                    device = await updater.get_device()
                    file = device.fw_file

                # setting the currently installed version based on the current assigned firmware / existing rollouts
                # is problematic. Better to assign custom action_id for each update (rollout id? firmware id? new id?).
                # Alternatively - but requires customization on the gateway side - use version reported by the gateway.
                await updater.update_fw_version(file)

            elif state == "failure":
                await updater.update_device_state("error")

                # not guaranteed to be the correct rollout - see comment above.
                rollout = await updater.get_rollout()
                if rollout:
                    rollout.failure_count += 1
                    await rollout.save()

    except KeyError:
        pass

    try:
        log = data["status"]["details"]
        await updater.update_log("\n".join(log))
    except KeyError:
        pass

    await updater.save()
    return {"id": str(action_id)}
