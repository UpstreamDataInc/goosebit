import pytest


@pytest.mark.asyncio
async def test_list_devices_uuid_asc(async_client, test_data):
    response = await async_client.get(f"/ui/bff/devices?order[0][dir]=asc&order[0][name]=uuid")

    assert response.status_code == 200
    devices = response.json()["data"]
    assert len(devices) == 2
    assert devices[0]["uuid"] == test_data["device_rollout"].uuid
    assert devices[1]["uuid"] == test_data["device_assigned"].uuid


@pytest.mark.asyncio
async def test_list_devices_uuid_desc(async_client, test_data):
    response = await async_client.get(f"/ui/bff/devices?order[0][dir]=desc&order[0][name]=uuid")

    assert response.status_code == 200
    devices = response.json()["data"]
    assert len(devices) == 2
    assert devices[0]["uuid"] == test_data["device_assigned"].uuid
    assert devices[1]["uuid"] == test_data["device_rollout"].uuid
