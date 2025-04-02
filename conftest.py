import logging
import os
import tempfile
from pathlib import Path

import pytest_asyncio
from aiocache import caches
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise
from tortoise.contrib.fastapi import RegisterTortoise

from goosebit import app
from goosebit.db.models import UpdateModeEnum, UpdateStateEnum

# Configure logging
logging.basicConfig(level=logging.WARN)

TORTOISE_CONF = {
    "connections": {"default": "sqlite://:memory:"},
    "apps": {
        "models": {
            "models": ["goosebit.db.models", "aerich.models"],
        },
    },
}


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clear_cache():
    await caches.get("default").clear()
    yield


@pytest_asyncio.fixture(scope="function")
async def test_app():
    async with RegisterTortoise(
        app=app,
        config=TORTOISE_CONF,
    ):
        yield app


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test", follow_redirects=True
    ) as client:
        login_data = {"username": "admin@goosebit.local", "password": "admin"}
        response = await client.post("/login", data=login_data, follow_redirects=True)
        assert response.status_code == 200

        data = response.json()
        client.cookies.set("session_id", data["access_token"])

        yield client


@pytest_asyncio.fixture(scope="function")
async def db():
    await Tortoise.init(config=TORTOISE_CONF)
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()
    await Tortoise.close_connections()


@pytest_asyncio.fixture(scope="function")
async def test_data(db):
    from goosebit.db.models import Device, Hardware, Rollout, Software

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        hardware = await Hardware.create(model="default", revision="default")

        temp_file_path = os.path.join(temp_dir, "software")
        with open(temp_file_path, "w") as temp_file:
            temp_file.write("Fake SWUpdate image")
        uri = Path(temp_file_path).as_uri()

        software_beta = await Software.create(
            version="1.0.0-beta2+build20",
            hash="dummy2",
            size=800,
            uri=uri,
        )
        await software_beta.compatibility.add(hardware)

        software_rc = await Software.create(
            version="1.0.0-rc2+build77",
            hash="dummy2",
            size=800,
            uri=uri,
        )
        await software_rc.compatibility.add(hardware)

        software_release = await Software.create(
            version="1",
            hash="dummy",
            size=1200,
            uri=uri,
        )
        await software_release.compatibility.add(hardware)

        rollout_default = await Rollout.create(software_id=software_release.id)

        device_rollout = await Device.create(
            id="device1",
            last_state=UpdateStateEnum.REGISTERED,
            update_mode=UpdateModeEnum.ROLLOUT,
            hardware=hardware,
        )

        device_assigned = await Device.create(
            id="device2",
            last_state=UpdateStateEnum.REGISTERED,
            update_mode=UpdateModeEnum.ASSIGNED,
            assigned_software=software_release,
            hardware=hardware,
            auth_token="auth_token1",
        )

        yield dict(
            hardware=hardware,
            software_release=software_release,
            software_rc=software_rc,
            software_beta=software_beta,
            rollout_default=rollout_default,
            device_rollout=device_rollout,
            device_assigned=device_assigned,
            device_authentication=device_assigned,
            device_no_authentication=device_rollout,
        )
