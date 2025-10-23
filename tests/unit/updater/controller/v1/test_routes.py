from typing import Any, Dict

import pytest
from httpx import AsyncClient

from goosebit.db.models import Device, Hardware, Software
from goosebit.device_manager import DeviceManager, get_device
from goosebit.settings import config

DEVICE_ID = "221326d9-7873-418e-960c-c074026a3b7c"


async def _api_device_update(
    async_client: AsyncClient, device: Device, update_attribute: str, update_value: Any
) -> None:
    response = await async_client.patch(
        "/ui/bff/devices",
        json={"devices": [f"{device.id}"], update_attribute: update_value},
    )
    assert response.status_code == 200


async def _api_device_get(async_client: AsyncClient, dev_id: str) -> Dict[str, Any]:
    response = await async_client.get("/api/v1/devices")
    assert response.status_code == 200
    devices = response.json()["devices"]
    return next(d for d in devices if d["id"] == dev_id)


async def _api_rollout_create(async_client: AsyncClient, feed: str, software: Software, paused: bool) -> None:
    response = await async_client.put(
        "/api/v1/rollouts",
        json={"name": "", "feed": feed, "software_id": software.id},
    )
    assert response.status_code == 200
    rollout_id = response.json()["id"]

    response = await async_client.patch(
        "/api/v1/rollouts",
        json={"ids": [rollout_id], "paused": paused},
    )
    assert response.status_code == 200


async def _api_rollouts_get(async_client: AsyncClient) -> Any:
    response = await async_client.get("/api/v1/rollouts")
    assert response.status_code == 200
    return response.json()


async def _poll_first_time(async_client: AsyncClient) -> str:
    response = await async_client.get(f"/DEFAULT/controller/v1/{DEVICE_ID}")
    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert data["config"]["polling"]["sleep"] == "00:00:10"
    assert "_links" in data
    config_url: str = data["_links"]["configData"]["href"]
    assert config_url == f"http://test/DEFAULT/controller/v1/{DEVICE_ID}/configData"
    return config_url


async def _register(async_client: AsyncClient, config_url: str) -> None:
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


async def _poll(
    async_client: AsyncClient, device_id: str, software: Software | None, expect_update: bool = True
) -> str | None:
    response = await async_client.get(f"/DEFAULT/controller/v1/{device_id}")

    assert response.status_code == 200
    data = response.json()
    if expect_update:
        assert data["config"]["polling"]["sleep"] == config.poll_time
        assert "deploymentBase" in data["_links"], "expected update, but none available"
        deployment_base: str = data["_links"]["deploymentBase"]["href"]
        assert software is not None
        assert deployment_base == f"http://test/DEFAULT/controller/v1/{device_id}/deploymentBase/{software.id}"
        return deployment_base
    else:
        assert data["config"]["polling"]["sleep"] == config.poll_time
        assert data["_links"] == {}
        return None


async def _retrieve_software_url(
    async_client: AsyncClient, device_id: str, deployment_base: str, software: Software
) -> str:
    response = await async_client.get(deployment_base)
    assert response.status_code == 200
    data = response.json()
    assert data["deployment"]["download"] == "forced"
    assert data["deployment"]["update"] == "forced"
    assert data["id"] == str(software.id)
    assert (
        data["deployment"]["chunks"][0]["artifacts"][0]["_links"]["download"]["href"]
        == f"http://test/DEFAULT/controller/v1/{device_id}/download"
    )
    assert data["deployment"]["chunks"][0]["artifacts"][0]["hashes"]["sha1"] == software.hash
    assert data["deployment"]["chunks"][0]["artifacts"][0]["size"] == software.size

    download_url: str = data["deployment"]["chunks"][0]["artifacts"][0]["_links"]["download"]["href"]
    return download_url


async def _feedback(
    async_client: AsyncClient, device_id: str, software: Software, finished: str, execution: str, details: str = ""
) -> None:
    response = await async_client.post(
        f"/DEFAULT/controller/v1/{device_id}/deploymentBase/{software.id}/feedback",
        json={
            "id": software.id,
            "status": {
                "result": {"finished": finished},
                "execution": execution,
                "details": [details],
            },
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_device(async_client: AsyncClient, test_data: Dict[str, Any]) -> None:
    config_url = await _poll_first_time(async_client)

    await _register(async_client, config_url)

    await _poll(async_client, DEVICE_ID, None, False)

    device_api = await _api_device_get(async_client, DEVICE_ID)
    assert device_api["last_state"] == "Registered"
    assert device_api["sw_version"] == "8.8.1-12-g302f635+189128"
    assert device_api["hardware"]["model"] == "smart-gateway-mt7688"
    assert device_api["hardware"]["revision"] == "default"


@pytest.mark.asyncio
@pytest.mark.parametrize("delete_software", [False, True])
async def test_rollout_full(async_client: AsyncClient, test_data: Dict[str, Any], delete_software: bool) -> None:
    device = test_data["device_rollout"]
    software = test_data["software_release"]
    rollout = test_data["rollout_default"]

    deployment_base = await _poll(async_client, device.id, software)
    assert deployment_base is not None

    await _retrieve_software_url(async_client, device.id, deployment_base, software)

    # confirm installation start (in reality: several of similar posts)
    await _feedback(async_client, device.id, software, "none", "proceeding")
    device_api = await _api_device_get(async_client, device.id)
    assert device_api["last_state"] == "Running"

    # edge case: remove software during update
    if delete_software:
        await Software.delete(software)

    # report finished installation
    await _feedback(async_client, device.id, software, "success", "closed")
    device_api = await _api_device_get(async_client, device.id)
    assert device_api["last_state"] == "Finished"

    if not delete_software:
        assert device_api["sw_version"] == software.version

        await rollout.refresh_from_db()
        rollouts = await _api_rollouts_get(async_client)
        assert rollouts["rollouts"][0]["success_count"] == 1
        assert rollouts["rollouts"][0]["failure_count"] == 0


@pytest.mark.asyncio
async def test_rollout_signalling_download_failure(async_client: AsyncClient, test_data: Dict[str, Any]) -> None:
    device = test_data["device_rollout"]
    software = test_data["software_release"]

    deployment_base = await _poll(async_client, device.id, software)
    assert deployment_base is not None

    software_url = await _retrieve_software_url(async_client, device.id, deployment_base, software)

    # confirm installation start (in reality: several of similar posts)
    await _feedback(async_client, device.id, software, "none", "proceeding")
    device_api = await _api_device_get(async_client, device.id)
    assert device_api["last_state"] == "Running"

    # HEAD /api/v1/download/1 HTTP/1.1 (reason not clear)
    response = await async_client.head(software_url)
    assert response.status_code == 200
    assert response.headers["Content-Length"] == "1200"

    # GET /api/v1/download/1 HTTP/1.1
    response = await async_client.get(software_url)
    assert response.status_code == 200

    # report failure
    await _feedback(async_client, device.id, software, "failure", "closed")
    device_api = await _api_device_get(async_client, device.id)
    assert device_api["last_state"] == "Error"


@pytest.mark.asyncio
async def test_rollout_selection(async_client: AsyncClient, test_data: Dict[str, Any]) -> None:
    device = test_data["device_rollout"]
    await _api_device_update(async_client, device, "feed", "qa")

    software_beta = test_data["software_beta"]
    software_rc = test_data["software_rc"]
    software_release = test_data["software_release"]

    await _poll(async_client, device.id, None, False)

    await _api_rollout_create(async_client, "qa", software_beta, False)
    await _poll(async_client, device.id, software_beta)

    await _api_rollout_create(async_client, "live", software_rc, False)
    await _poll(async_client, device.id, software_beta)

    await _api_rollout_create(async_client, "qa", software_release, True)
    await _poll(async_client, device.id, software_beta)

    await _api_rollout_create(async_client, "qa", software_release, False)
    await _poll(async_client, device.id, software_release)


@pytest.mark.asyncio
async def test_latest(async_client: AsyncClient, test_data: Dict[str, Any]) -> None:
    device = test_data["device_rollout"]
    software = test_data["software_release"]

    await _api_device_update(async_client, device, "software", "latest")

    deployment_base = await _poll(async_client, device.id, software)
    assert deployment_base is not None

    await _retrieve_software_url(async_client, device.id, deployment_base, software)

    # confirm installation start (in reality: several of similar posts)
    await _feedback(async_client, device.id, software, "none", "proceeding")
    device_api = await _api_device_get(async_client, device.id)
    assert device_api["last_state"] == "Running"

    # report finished installation
    await _feedback(async_client, device.id, software, "success", "closed")
    device_api = await _api_device_get(async_client, device.id)
    assert device_api["last_state"] == "Finished"
    assert device_api["sw_version"] == software.version


@pytest.mark.asyncio
async def test_latest_with_no_software_available(async_client: AsyncClient, test_data: Dict[str, Any]) -> None:
    device = test_data["device_rollout"]

    await _api_device_update(async_client, device, "software", "latest")

    fake_hardware = await Hardware.create(model="does-not-exist", revision="default")
    device.hardware_id = fake_hardware.id
    await device.save()

    await _poll(async_client, device.id, None, False)


@pytest.mark.asyncio
async def test_pinned(async_client: AsyncClient, test_data: Dict[str, Any]) -> None:
    device = test_data["device_rollout"]

    await _api_device_update(async_client, device, "pinned", True)

    await _poll(async_client, device.id, None, False)


@pytest.mark.asyncio
async def test_up_to_date(async_client: AsyncClient, test_data: Dict[str, Any]) -> None:
    device = test_data["device_rollout"]
    software = test_data["software_release"]

    await _api_device_update(async_client, device, "software", "latest")

    device = await get_device(dev_id=device.id)
    await DeviceManager.update_sw_version(device, software.version)

    await _poll(async_client, device.id, None, False)


async def _assert_log_lines(async_client: AsyncClient, device: Device, expected_line_count: int) -> None:
    response = await async_client.get(f"/ui/bff/devices/{device.id}/log")
    assert response.status_code == 200

    log = response.json()["log"]
    if log is None:
        assert expected_line_count == 0
    else:
        actual_line_count = log.count("\n")
        if not log.endswith("\n"):
            actual_line_count += 1

        assert actual_line_count == expected_line_count


@pytest.mark.asyncio
async def test_update_logs_and_progress(async_client: AsyncClient, test_data: Dict[str, Any]) -> None:
    device = test_data["device_rollout"]
    software = test_data["software_release"]

    await _api_device_update(async_client, device, "software", "latest")

    deployment_base = await _poll(async_client, device.id, software)
    assert deployment_base is not None
    await _assert_log_lines(async_client, device, 0)

    await _retrieve_software_url(async_client, device.id, deployment_base, software)

    # confirm installation start (in reality: several of similar posts)
    await _feedback(async_client, device.id, software, "none", "proceeding", "Downloaded 7%")
    await _assert_log_lines(async_client, device, 1)
    device_api = await _api_device_get(async_client, device.id)
    assert device_api["last_state"] == "Running"
    assert device_api["progress"] == 7

    await _feedback(async_client, device.id, software, "none", "proceeding", "Installing Update Chunk Artifacts.")
    await _assert_log_lines(async_client, device, 2)

    # report finished installation
    await _feedback(async_client, device.id, software, "success", "closed")
    device_api = await _api_device_get(async_client, device.id)
    assert device_api["progress"] == 100
    assert device_api["last_state"] == "Finished"
    assert device_api["sw_version"] == software.version

    await _assert_log_lines(async_client, device, 3)

    # fake installation start confirmation to check clearing of logs
    await _feedback(async_client, device.id, software, "none", "proceeding", "Downloaded 1%")
    await _assert_log_lines(async_client, device, 1)
