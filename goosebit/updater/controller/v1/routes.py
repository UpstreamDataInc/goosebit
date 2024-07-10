import json

from fastapi import APIRouter, Depends
from fastapi.requests import Request

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
    return {
        "config": {"polling": {"sleep": updater.poll_time}},
        "_links": {
            "deploymentBase": {
                "href": str(
                    request.url_for(
                        "deployment_base", tenant=tenant, dev_id=dev_id, action_id=1
                    )
                )
            },
        },
    }


@router.put("/{dev_id}/configData")
async def config_data(
    request: Request,
    dev_id: str,
    updater: UpdateManager = Depends(get_update_manager),
):
    data = await request.json()
    # TODO: make standard schema to deal with this
    print(data)
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
        state = data["status"]["result"]["finished"]
        await updater.update_device_state(state)
    except KeyError:
        pass

    try:
        log = data["status"]["details"]
        await updater.update_log("\n".join(log))
    except KeyError:
        pass

    await updater.save()
    return {"id": str(action_id)}
