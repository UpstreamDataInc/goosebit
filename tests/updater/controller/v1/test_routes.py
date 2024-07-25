import pytest

UUID = "221326d9-7873-418e-960c-c074026a3b7c"


@pytest.mark.asyncio
async def test_register_device(async_client, test_data):
    # first poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{UUID}")

    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert "_links" in data
    configUrl = data["_links"]["configData"]["href"]
    assert configUrl == f"http://test/DEFAULT/controller/v1/{UUID}/configData"

    # register device
    response = await async_client.put(
        configUrl,
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
async def test_rollout_and_download_info(async_client, test_data):
    device = test_data["device_none"]
    firmware = test_data["firmware_latest"]

    # poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{device.uuid}")

    assert response.status_code == 200
    data = response.json()
    deploymentBase = data["_links"]["deploymentBase"]["href"]
    assert (
        deploymentBase
        == f"http://test/DEFAULT/controller/v1/{device.uuid}/deploymentBase/1"
    )
    # TODO: activate this test once the action_id matches the firmware id
    # assert (
    #     deploymentBase
    #     == f"http://test/DEFAULT/controller/v1/{device.uuid}/deploymentBase/{firmware.id}"
    # )

    # retrieve firmware
    response = await async_client.get(deploymentBase)

    # assert response.status_code == 200
    data = response.json()
    assert data["deployment"]["download"] == "forced"
    assert data["deployment"]["update"] == "forced"
    assert data["id"] == str(1)
    # assert data["id"] == str(firmware.id)
    assert (
        data["deployment"]["chunks"][0]["artifacts"][0]["_links"]["download"]["href"]
        == f"http://test/api/download/by_id/{firmware.id}"
    )
    assert (
        data["deployment"]["chunks"][0]["artifacts"][0]["hashes"]["sha1"]
        == firmware.hash
    )
    assert data["deployment"]["chunks"][0]["artifacts"][0]["size"] == firmware.size


@pytest.mark.asyncio
async def test_latest(async_client, test_data):
    device = test_data["device_latest"]
    # firmware = test_data["firmware_latest"]

    # poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{device.uuid}")

    assert response.status_code == 200
    data = response.json()
    deploymentBase = data["_links"]["deploymentBase"]["href"]
    assert (
        deploymentBase
        == f"http://test/DEFAULT/controller/v1/{device.uuid}/deploymentBase/1"
    )
    # TODO: activate this test once the action_id matches the firmware id
    # assert (
    #     deploymentBase
    #     == f"http://test/DEFAULT/controller/v1/{device.uuid}/deploymentBase/{firmware.id}"
    # )


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
    device.fw_version = firmware.version
    await device.save()

    # poll
    response = await async_client.get(f"/DEFAULT/controller/v1/{device.uuid}")

    assert response.status_code == 200
    data = response.json()
    assert data["_links"] == {}
