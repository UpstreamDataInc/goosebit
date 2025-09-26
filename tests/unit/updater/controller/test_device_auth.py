from typing import Any, Dict

import pytest
from httpx import AsyncClient

from goosebit.db.models import Device
from goosebit.settings import config
from goosebit.settings.schema import DeviceAuthMode


async def _api_device_get(device_auth_async_client: AsyncClient, dev_id: str) -> Dict[str, Any]:
    response = await device_auth_async_client.get("/api/v1/devices")
    assert response.status_code == 200
    devices = response.json()["devices"]
    return next(d for d in devices if d["id"] == dev_id)


async def _api_device_update(
    device_auth_async_client: AsyncClient, device: Device, update_attribute: str, update_value: Any
) -> None:
    response = await device_auth_async_client.patch(
        "/ui/bff/devices",
        json={"devices": [f"{device.id}"], update_attribute: update_value},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_poll_strict_with_no_auth_device_with_no_auth(
    async_client: AsyncClient, test_data: Dict[str, Any], monkeypatch: Any
) -> None:
    device = test_data["device_no_authentication"]
    monkeypatch.setattr(config.device_auth, "enable", True)
    monkeypatch.setattr(config.device_auth, "mode", DeviceAuthMode.STRICT)

    response = await async_client.get(f"/DEFAULT/controller/v1/{device.id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_poll_strict_with_no_auth_device_with_auth(
    async_client: AsyncClient, test_data: Dict[str, Any], monkeypatch: Any
) -> None:
    device = test_data["device_authentication"]
    monkeypatch.setattr(config.device_auth, "enable", True)
    monkeypatch.setattr(config.device_auth, "mode", DeviceAuthMode.STRICT)

    response = await async_client.get(f"/DEFAULT/controller/v1/{device.id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_poll_strict_with_auth_device_with_auth(
    async_client: AsyncClient, test_data: Dict[str, Any], monkeypatch: Any
) -> None:
    device = test_data["device_authentication"]
    monkeypatch.setattr(config.device_auth, "enable", True)
    monkeypatch.setattr(config.device_auth, "mode", DeviceAuthMode.STRICT)

    response = await async_client.get(
        f"/DEFAULT/controller/v1/{device.id}", headers={"Authorization": f"TargetToken {device.auth_token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_poll_lax_with_no_auth_device_with_no_auth(
    async_client: AsyncClient, test_data: Dict[str, Any], monkeypatch: Any
) -> None:
    device = test_data["device_no_authentication"]
    monkeypatch.setattr(config.device_auth, "enable", True)
    monkeypatch.setattr(config.device_auth, "mode", DeviceAuthMode.LAX)

    response = await async_client.get(f"/DEFAULT/controller/v1/{device.id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_poll_lax_with_no_auth_device_with_auth(
    async_client: AsyncClient, test_data: Dict[str, Any], monkeypatch: Any
) -> None:
    device = test_data["device_authentication"]
    monkeypatch.setattr(config.device_auth, "enable", True)
    monkeypatch.setattr(config.device_auth, "mode", DeviceAuthMode.LAX)

    response = await async_client.get(f"/DEFAULT/controller/v1/{device.id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_poll_lax_with_auth_device_with_auth(
    async_client: AsyncClient, test_data: Dict[str, Any], monkeypatch: Any
) -> None:
    device = test_data["device_authentication"]
    monkeypatch.setattr(config.device_auth, "enable", True)
    monkeypatch.setattr(config.device_auth, "mode", DeviceAuthMode.LAX)

    response = await async_client.get(
        f"/DEFAULT/controller/v1/{device.id}", headers={"Authorization": f"TargetToken {device.auth_token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_poll_setup_with_no_auth(async_client: AsyncClient, test_data: Dict[str, Any], monkeypatch: Any) -> None:
    device = test_data["device_no_authentication"]
    monkeypatch.setattr(config.device_auth, "enable", True)
    monkeypatch.setattr(config.device_auth, "mode", DeviceAuthMode.SETUP)

    response = await async_client.get(f"/DEFAULT/controller/v1/{device.id}")
    assert response.status_code == 200

    # device should not have changed
    device_api = await _api_device_get(async_client, device.id)
    assert device_api["auth_token"] is None


@pytest.mark.asyncio
async def test_poll_setup_with_auth_add_device_auth(
    async_client: AsyncClient, test_data: Dict[str, Any], monkeypatch: Any
) -> None:
    device = test_data["device_no_authentication"]
    monkeypatch.setattr(config.device_auth, "enable", True)
    monkeypatch.setattr(config.device_auth, "mode", DeviceAuthMode.SETUP)

    response = await async_client.get(f"/DEFAULT/controller/v1/{device.id}")
    assert response.status_code == 200

    token = "testing123"
    await async_client.get(f"/DEFAULT/controller/v1/{device.id}", headers={"Authorization": f"TargetToken {token}"})

    device_api = await _api_device_get(async_client, device.id)
    assert device_api["auth_token"] == token

    await _api_device_update(async_client, device, "auth_token", None)


@pytest.mark.asyncio
async def test_poll_setup_with_auth_update_device_auth(
    async_client: AsyncClient, test_data: Dict[str, Any], monkeypatch: Any
) -> None:
    device = test_data["device_authentication"]
    old_token = device.auth_token

    monkeypatch.setattr(config.device_auth, "enable", True)
    monkeypatch.setattr(config.device_auth, "mode", DeviceAuthMode.SETUP)

    response = await async_client.get(f"/DEFAULT/controller/v1/{device.id}")
    assert response.status_code == 200

    token = "testing123"
    await async_client.get(f"/DEFAULT/controller/v1/{device.id}", headers={"Authorization": f"TargetToken {token}"})

    device_api = await _api_device_get(async_client, device.id)
    assert device_api["auth_token"] == token

    await _api_device_update(async_client, device, "auth_token", old_token)


@pytest.mark.asyncio
async def test_poll_setup_with_no_auth_no_change(
    async_client: AsyncClient, test_data: Dict[str, Any], monkeypatch: Any
) -> None:
    device = test_data["device_authentication"]

    monkeypatch.setattr(config.device_auth, "enable", True)
    monkeypatch.setattr(config.device_auth, "mode", DeviceAuthMode.SETUP)

    response = await async_client.get(f"/DEFAULT/controller/v1/{device.id}")
    assert response.status_code == 200

    await async_client.get(f"/DEFAULT/controller/v1/{device.id}")

    device_api = await _api_device_get(async_client, device.id)
    assert device_api["auth_token"] == device.auth_token
