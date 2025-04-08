import pytest

from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS


@pytest.mark.asyncio
async def test_create_user(async_client, test_data):
    user_to_create = {"username": "created@goosebit.test", "permissions": [GOOSEBIT_PERMISSIONS["device"]["read"]()]}

    response = await async_client.post(f"/api/v1/settings/users", json={"password": "testcreated", **user_to_create})
    assert response.status_code == 200

    user_to_create["enabled"] = True

    response = await async_client.get(f"/api/v1/settings/users")
    users = response.json()
    assert user_to_create in users["users"]
