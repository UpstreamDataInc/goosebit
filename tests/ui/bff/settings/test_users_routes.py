import pytest


@pytest.mark.asyncio
async def test_list_users_username_asc(async_client, test_data):
    response = await async_client.get(f"/ui/bff/settings/users?order[0][dir]=asc&order[0][name]=username")

    assert response.status_code == 200
    users = response.json()["data"]
    assert len(users) == 2
    assert users[0]["username"] == test_data["user_admin"].username
    assert users[1]["username"] == test_data["user_read_only"].username


@pytest.mark.asyncio
async def test_list_users_username_desc(async_client, test_data):
    response = await async_client.get(f"/ui/bff/settings/users?order[0][dir]=desc&order[0][name]=username")

    assert response.status_code == 200
    users = response.json()["data"]
    assert len(users) == 2
    assert users[0]["username"] == test_data["user_read_only"].username
    assert users[1]["username"] == test_data["user_admin"].username
