import pytest


@pytest.mark.asyncio
async def test_list_software_version_asc(async_client, test_data):
    response = await async_client.get(f"/ui/bff/software?order[0][dir]=asc&order[0][name]=version")

    assert response.status_code == 200
    software = response.json()["data"]
    assert len(software) == 3
    assert software[0]["version"] == test_data["software_beta"].version
    assert software[1]["version"] == test_data["software_rc"].version
    assert software[2]["version"] == test_data["software_release"].version


@pytest.mark.asyncio
async def test_list_software_version_desc(async_client, test_data):
    response = await async_client.get(f"/ui/bff/software?order[0][dir]=desc&order[0][name]=version")

    assert response.status_code == 200
    software = response.json()["data"]
    assert len(software) == 3
    assert software[0]["version"] == test_data["software_release"].version
    assert software[1]["version"] == test_data["software_rc"].version
    assert software[2]["version"] == test_data["software_beta"].version
