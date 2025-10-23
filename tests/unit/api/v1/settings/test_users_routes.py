from typing import Any

import pytest

from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS


@pytest.mark.asyncio
async def test_create_user(async_client: Any, test_data: Any) -> None:
    user_to_create = {"username": "created@goosebit.test", "permissions": [GOOSEBIT_PERMISSIONS["device"]["read"]()]}

    response = await async_client.put("/api/v1/settings/users", json={"password": "testcreated", **user_to_create})
    assert response.status_code == 200

    user_to_create["enabled"] = True  # type: ignore[assignment]

    response = await async_client.get("/api/v1/settings/users")
    users = response.json()
    assert user_to_create in users["users"]
