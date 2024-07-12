import json

from fastapi import APIRouter, Depends
from fastapi.requests import Request

from goosebit.updater.manager import UpdateManager, get_update_manager

# v1 is hardware revision
router = APIRouter(prefix="/{revision}")


@router.get("/{dev_id}")
async def polling(
    request: Request,
    tenant: str,
    revision: str,
    dev_id: str,
    updater: UpdateManager = Depends(get_update_manager),
):
    links = {}

    if updater.device.last_state == "unknown":
        # device registration
        sleep = "00:00:10"  # ensure that device will check back soon after registration
        links["configData"] = {
            "href": str(
                request.url_for(
                    "config_data",
                    tenant=tenant,
                    revision=revision,
                    dev_id=dev_id,
                )
            )
        }

    else:
        # update poll
        sleep = updater.poll_time
        update = await updater.get_update_mode()
        if update != "skip":
            links["deploymentBase"] = {
                "href": str(
                    request.url_for(
                        "deployment_base",
                        tenant=tenant,
                        revision=revision,
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
    revision: str,
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
    revision: str,
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
            "chunks": artifact.generate_chunk(
                request, tenant=tenant, revision=revision, dev_id=dev_id
            ),
        },
    }


@router.post("/{dev_id}/deploymentBase/{action_id}/feedback")
async def deployment_feedback(
    request: Request,
    tenant: str,
    revision: str,
    dev_id: str,
    action_id: int,
    updater: UpdateManager = Depends(get_update_manager),
):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return
    try:
        state = data["status"]["result"]["finished"]
        await updater.update_device_state(state)
        if state == "success":
            file = await updater.get_update_file()
            await updater.update_fw_version(file.name)
    except KeyError:
        pass

    try:
        log = data["status"]["details"]
        await updater.update_log("\n".join(log))
    except KeyError:
        pass

    await updater.save()
    return {"id": str(action_id)}
