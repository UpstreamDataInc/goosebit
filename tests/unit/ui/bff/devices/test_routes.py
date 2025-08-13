import pytest


@pytest.mark.asyncio
async def test_list_devices_id_asc(async_client, test_data):
    response = await async_client.get(f"/ui/bff/devices?order[0][dir]=asc&order[0][name]=id")

    assert response.status_code == 200
    devices = response.json()["data"]
    assert len(devices) == 2
    assert devices[0]["id"] == test_data["device_rollout"].id
    assert devices[1]["id"] == test_data["device_assigned"].id


@pytest.mark.asyncio
async def test_list_devices_id_desc(async_client, test_data):
    response = await async_client.get(f"/ui/bff/devices?order[0][dir]=desc&order[0][name]=id")

    assert response.status_code == 200
    devices = response.json()["data"]
    assert len(devices) == 2
    assert devices[0]["id"] == test_data["device_assigned"].id
    assert devices[1]["id"] == test_data["device_rollout"].id
