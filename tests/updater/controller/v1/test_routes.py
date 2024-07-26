import pytest

from goosebit.models import Hardware
from goosebit.updater.manager import get_update_manager

UUID = "221326d9-7873-418e-960c-c074026a3b7c"


@pytest.mark.asyncio
async def test_register_device(async_client, test_data):
    # first poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{UUID}")

    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert "_links" in data
    config_url = data["_links"]["configData"]["href"]
    assert config_url == f"http://test/DEFAULT/controller/v1/{UUID}/configData"

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
                "hw_model": "smart-gateway-mt7688",
                "installed_version": "8.8.1-12-g302f635+189128",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"]
    assert data["message"] == "Updated swupdate data."

    # second poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{UUID}")

    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert data["_links"] == {}


@pytest.mark.asyncio
async def test_rollout_signalling_failure(async_client, test_data):
    device = test_data["device_rollout"]
    firmware = test_data["firmware_latest"]

    # poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{device.uuid}")

    assert response.status_code == 200
    data = response.json()
    deployment_base = data["_links"]["deploymentBase"]["href"]
    assert (
        deployment_base
        == f"http://test/DEFAULT/controller/v1/{device.uuid}/deploymentBase/{firmware.id}"
    )

    # retrieve firmware
    response = await async_client.get(deployment_base)

    assert response.status_code == 200
    data = response.json()
    assert data["deployment"]["download"] == "forced"
    assert data["deployment"]["update"] == "forced"
    assert data["id"] == str(firmware.id)
    assert (
        data["deployment"]["chunks"][0]["artifacts"][0]["_links"]["download"]["href"]
        == f"http://test/api/download/{firmware.id}"
    )
    assert (
        data["deployment"]["chunks"][0]["artifacts"][0]["hashes"]["sha1"]
        == firmware.hash
    )
    assert data["deployment"]["chunks"][0]["artifacts"][0]["size"] == firmware.size

    # confirm installation start (in reality: several of simular posts)
    response = await async_client.post(
        f"/DEFAULT/controller/v1/{device.uuid}/deploymentBase/{firmware.id}/feedback",
        json={
            "id": firmware.id,
            "status": {
                "result": {"finished": "none"},
                "execution": "proceeding",
                "details": ["Installing Update Chunk Artifacts."],
            },
        },
    )
    assert response.status_code == 200
    await device.refresh_from_db()
    assert device.last_state == "running"

    # HEAD /api/download/1 HTTP/1.1 (reason not clear)
    response = await async_client.head(f"/api/download/{firmware.id}")
    assert response.status_code == 405

    # GET /api/download/1 HTTP/1.1
    response = await async_client.get(f"/api/download/{firmware.id}")
    assert response.status_code == 200

    # report failure
    response = await async_client.post(
        f"/DEFAULT/controller/v1/{device.uuid}/deploymentBase/{firmware.id}/feedback",
        json={
            "id": firmware.id,
            "status": {
                "result": {"finished": "failure"},
                "execution": "closed",
                "details": ["No suitable .swu image found"],
            },
        },
    )
    assert response.status_code == 200

    await device.refresh_from_db()
    assert device.last_state == "error"


@pytest.mark.asyncio
async def test_latest(async_client, test_data):
    device = test_data["device_latest"]
    firmware = test_data["firmware_latest"]

    # poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{device.uuid}")

    assert response.status_code == 200
    data = response.json()
    deployment_base = data["_links"]["deploymentBase"]["href"]
    assert (
        deployment_base
        == f"http://test/DEFAULT/controller/v1/{device.uuid}/deploymentBase/{firmware.id}"
    )


@pytest.mark.asyncio
async def test_latest_with_no_firmware_available(async_client, test_data):
    device = test_data["device_latest"]

    fake_hardware = await Hardware.create(model="does-not-exist", revision="default")
    device.hardware_id = fake_hardware.id
    await device.save()

    # poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{device.uuid}")

    assert response.status_code == 200
    data = response.json()
    assert data["_links"] == {}


@pytest.mark.asyncio
async def test_pinned(async_client, test_data):
    device = test_data["device_pinned"]

    # poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{device.uuid}")

    assert response.status_code == 200
    data = response.json()
    assert data["_links"] == {}


@pytest.mark.asyncio
async def test_up_to_date(async_client, test_data):
    device = test_data["device_latest"]
    firmware = test_data["firmware_latest"]
    manager = await get_update_manager(dev_id=device.uuid)
    await manager.update_fw_version(firmware.version)

    # poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{device.uuid}")

    assert response.status_code == 200
    data = response.json()
    assert data["_links"] == {}
