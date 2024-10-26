import pytest

from goosebit.db.models import Hardware, Software
from goosebit.settings import GooseBitSettings
from goosebit.updater.manager import get_update_manager

UUID = "221326d9-7873-418e-960c-c074026a3b7c"

config = GooseBitSettings()


async def _api_device_update(async_client, device, update_attribute, update_value):
    response = await async_client.patch(
        f"/ui/bff/devices",
        json={"devices": [f"{device.uuid}"], update_attribute: update_value},
    )
    assert response.status_code == 200


async def _api_device_get(async_client, dev_id):
    response = await async_client.get("/api/v1/devices")
    assert response.status_code == 200
    devices = response.json()["devices"]
    return next(d for d in devices if d["uuid"] == dev_id)


async def _api_rollout_create(async_client, feed, software, paused):
    response = await async_client.post(
        f"/api/v1/rollouts",
        json={"name": "", "feed": feed, "software_id": software.id},
    )
    assert response.status_code == 200
    rollout_id = response.json()["id"]

    response = await async_client.patch(
        f"/api/v1/rollouts",
        json={"ids": [rollout_id], "paused": paused},
    )
    assert response.status_code == 200


async def _api_rollouts_get(async_client):
    response = await async_client.get("/api/v1/rollouts")
    assert response.status_code == 200
    return response.json()


async def _poll_first_time(async_client):
    response = await async_client.get(f"/ddi/controller/v1/{UUID}")
    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert data["config"]["polling"]["sleep"] == config.poll_time_registration
    assert "_links" in data
    config_url = data["_links"]["configData"]["href"]
    assert config_url == f"http://test/ddi/controller/v1/{UUID}/configData"
    return config_url


async def _register(async_client, config_url):
    # register device
    response = await async_client.put(
        config_url,
        json={
            "id": "",
            "status": {
                "result": {"finished": "success"},
                "execution": "closed",
                "details": [""],
            },
            "data": {
                "hw_boardname": "smart-gateway-mt7688",
                "sw_version": "8.8.1-12-g302f635+189128",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"]
    assert data["message"] == "Updated swupdate data."


async def _poll(async_client, device_uuid, software: Software | None, expect_update=True):
    response = await async_client.get(f"/ddi/controller/v1/{device_uuid}")

    assert response.status_code == 200
    data = response.json()
    if expect_update:
        assert data["config"]["polling"]["sleep"] == config.poll_time_updating
        assert "deploymentBase" in data["_links"], "expected update, but none available"
        deployment_base = data["_links"]["deploymentBase"]["href"]
        assert software is not None
        assert deployment_base == f"http://test/ddi/controller/v1/{device_uuid}/deploymentBase/{software.id}"
        return deployment_base
    else:
        assert data["config"]["polling"]["sleep"] == config.poll_time_default
        assert data["_links"] == {}
        return None


async def _retrieve_software_url(async_client, device_uuid, deployment_base, software):
    response = await async_client.get(deployment_base)
    assert response.status_code == 200
    data = response.json()
    assert data["deployment"]["download"] == "forced"
    assert data["deployment"]["update"] == "forced"
    assert data["id"] == str(software.id)
    assert (
        data["deployment"]["chunks"][0]["artifacts"][0]["_links"]["download"]["href"]
        == f"http://test/ddi/controller/v1/{device_uuid}/download"
    )
    assert data["deployment"]["chunks"][0]["artifacts"][0]["hashes"]["sha1"] == software.hash
    assert data["deployment"]["chunks"][0]["artifacts"][0]["size"] == software.size

    return data["deployment"]["chunks"][0]["artifacts"][0]["_links"]["download"]["href"]


async def _feedback(async_client, device_uuid, software, finished, execution):
    response = await async_client.post(
        f"/ddi/controller/v1/{device_uuid}/deploymentBase/{software.id}/feedback",
        json={
            "id": software.id,
            "status": {
                "result": {"finished": finished},
                "execution": execution,
                "details": [""],
            },
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_device(async_client, test_data):
    config_url = await _poll_first_time(async_client)

    await _register(async_client, config_url)

    await _poll(async_client, UUID, None, False)

    device_api = await _api_device_get(async_client, UUID)
    assert device_api["last_state"] == "Registered"
    assert device_api["sw_version"] == "8.8.1-12-g302f635+189128"
    assert device_api["hw_model"] == "smart-gateway-mt7688"
    assert device_api["hw_revision"] == "default"


@pytest.mark.asyncio
async def test_rollout_full(async_client, test_data):
    device = test_data["device_rollout"]
    software = test_data["software_release"]
    rollout = test_data["rollout_default"]

    deployment_base = await _poll(async_client, device.uuid, software)

    await _retrieve_software_url(async_client, device.uuid, deployment_base, software)

    # confirm installation start (in reality: several of similar posts)
    await _feedback(async_client, device.uuid, software, "none", "proceeding")
    device_api = await _api_device_get(async_client, device.uuid)
    assert device_api["last_state"] == "Running"

    # report finished installation
    await _feedback(async_client, device.uuid, software, "success", "closed")
    device_api = await _api_device_get(async_client, device.uuid)
    assert device_api["last_state"] == "Finished"
    assert device_api["sw_version"] == software.version

    await rollout.refresh_from_db()
    rollouts = await _api_rollouts_get(async_client)
    assert rollouts["rollouts"][0]["success_count"] == 1
    assert rollouts["rollouts"][0]["failure_count"] == 0


@pytest.mark.asyncio
async def test_rollout_signalling_download_failure(async_client, test_data):
    device = test_data["device_rollout"]
    software = test_data["software_release"]

    deployment_base = await _poll(async_client, device.uuid, software)

    software_url = await _retrieve_software_url(async_client, device.uuid, deployment_base, software)

    # confirm installation start (in reality: several of similar posts)
    await _feedback(async_client, device.uuid, software, "none", "proceeding")
    device_api = await _api_device_get(async_client, device.uuid)
    assert device_api["last_state"] == "Running"

    # HEAD /api/v1/download/1 HTTP/1.1 (reason not clear)
    response = await async_client.head(software_url)
    assert response.status_code == 200
    assert response.headers["Content-Length"] == "1200"

    # GET /api/v1/download/1 HTTP/1.1
    response = await async_client.get(software_url)
    assert response.status_code == 200

    # report failure
    await _feedback(async_client, device.uuid, software, "failure", "closed")
    device_api = await _api_device_get(async_client, device.uuid)
    assert device_api["last_state"] == "Error"


@pytest.mark.asyncio
async def test_rollout_selection(async_client, test_data):
    device = test_data["device_rollout"]
    await _api_device_update(async_client, device, "feed", "qa")

    software_beta = test_data["software_beta"]
    software_rc = test_data["software_rc"]
    software_release = test_data["software_release"]

    await _poll(async_client, device.uuid, None, False)

    await _api_rollout_create(async_client, "qa", software_beta, False)
    await _poll(async_client, device.uuid, software_beta)

    await _api_rollout_create(async_client, "live", software_rc, False)
    await _poll(async_client, device.uuid, software_beta)

    await _api_rollout_create(async_client, "qa", software_release, True)
    await _poll(async_client, device.uuid, software_beta)

    await _api_rollout_create(async_client, "qa", software_release, False)
    await _poll(async_client, device.uuid, software_release)


@pytest.mark.asyncio
async def test_latest(async_client, test_data):
    device = test_data["device_rollout"]
    software = test_data["software_release"]

    await _api_device_update(async_client, device, "software", "latest")

    deployment_base = await _poll(async_client, device.uuid, software)

    await _retrieve_software_url(async_client, device.uuid, deployment_base, software)

    # confirm installation start (in reality: several of similar posts)
    await _feedback(async_client, device.uuid, software, "none", "proceeding")
    device_api = await _api_device_get(async_client, device.uuid)
    assert device_api["last_state"] == "Running"

    # report finished installation
    await _feedback(async_client, device.uuid, software, "success", "closed")
    device_api = await _api_device_get(async_client, device.uuid)
    assert device_api["last_state"] == "Finished"
    assert device_api["sw_version"] == software.version


@pytest.mark.asyncio
async def test_latest_with_no_software_available(async_client, test_data):
    device = test_data["device_rollout"]

    await _api_device_update(async_client, device, "software", "latest")

    fake_hardware = await Hardware.create(model="does-not-exist", revision="default")
    device.hardware_id = fake_hardware.id
    await device.save()

    await _poll(async_client, device.uuid, None, False)


@pytest.mark.asyncio
async def test_pinned(async_client, test_data):
    device = test_data["device_rollout"]

    await _api_device_update(async_client, device, "pinned", True)

    await _poll(async_client, device.uuid, None, False)


@pytest.mark.asyncio
async def test_up_to_date(async_client, test_data):
    device = test_data["device_rollout"]
    software = test_data["software_release"]

    await _api_device_update(async_client, device, "software", "latest")

    manager = await get_update_manager(dev_id=device.uuid)
    await manager.update_sw_version(software.version)

    await _poll(async_client, device.uuid, None, False)
