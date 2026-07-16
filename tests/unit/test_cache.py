from typing import Any

import pytest

from goosebit.cache import CACHE_TTL, Cache, cache
from goosebit.db.models import User
from goosebit.device_manager import DeviceManager
from goosebit.settings.schema import GooseBitSettings
from goosebit.users import UserManager, create_initial_user


@pytest.mark.asyncio
async def test_disabled_cache_is_noop() -> None:
    disabled = Cache(enabled=False)

    await disabled.set("key", "value")
    assert await disabled.get("key") is None

    # missing keys must not raise
    await disabled.delete("key")
    await disabled.clear()


@pytest.mark.asyncio
async def test_enabled_cache_round_trip() -> None:
    enabled = Cache(enabled=True)

    await enabled.set("key", "value")
    assert await enabled.get("key") == "value"

    await enabled.delete("key")
    assert await enabled.get("key") is None

    # deleting a key that was never cached must not raise
    await enabled.delete("never-cached")


@pytest.mark.asyncio
async def test_enabled_cache_set_applies_ttl() -> None:
    enabled = Cache(enabled=True)

    await enabled.set("key", "value")

    # an expiry TimerHandle exists only when a ttl was applied
    assert "key" in enabled._backend._handlers
    assert enabled._backend.ttl == CACHE_TTL


@pytest.mark.asyncio
async def test_device_manager_with_disabled_cache(db: None, monkeypatch: Any) -> None:
    monkeypatch.setattr(cache, "enabled", False)

    device = await DeviceManager.get_device("cache-test-device")
    assert await cache.get(device.id) is None

    await DeviceManager.update_name(device, "renamed")
    device = await DeviceManager.get_device("cache-test-device")
    assert device.name == "renamed"

    await DeviceManager.delete_devices([device.id])
    recreated = await DeviceManager.get_device("cache-test-device")
    assert recreated.name is None


@pytest.mark.asyncio
async def test_delete_device_that_was_never_cached(db: None) -> None:
    device = await DeviceManager.get_device("uncached-device")
    # simulate the entry expiring or the delete landing on a worker that never cached the device
    await cache.clear()

    await DeviceManager.delete_devices([device.id])


@pytest.mark.asyncio
async def test_user_manager_with_disabled_cache(db: None, monkeypatch: Any) -> None:
    monkeypatch.setattr(cache, "enabled", False)

    await create_initial_user(username="cache@goosebit.test", hashed_pwd="hash")
    user = await UserManager.get_user("cache@goosebit.test")
    assert user is not None
    assert await cache.get(user.username) is None

    await UserManager.update_enabled(user, False)
    user = await UserManager.get_user("cache@goosebit.test")
    assert user.enabled is False

    await UserManager.delete_users([user.username])
    assert await UserManager.get_user("cache@goosebit.test") is None


@pytest.mark.asyncio
async def test_device_id_does_not_shadow_username(db: None) -> None:
    username = "collision@goosebit.test"
    await create_initial_user(username=username, hashed_pwd="hash")
    # dev_id equal to a username must not poison the user cache
    await DeviceManager.get_device(username)
    user = await UserManager.get_user(username)
    assert isinstance(user, User)


def test_cache_enabled_setting(monkeypatch: Any) -> None:
    assert GooseBitSettings().cache.enabled is True

    monkeypatch.setenv("GOOSEBIT_CACHE__ENABLED", "false")
    assert GooseBitSettings().cache.enabled is False
