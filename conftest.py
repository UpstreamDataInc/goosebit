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
from goosebit.models import UpdateModeEnum, UpdateStateEnum

# Configure logging
logging.basicConfig(level=logging.WARN)

TORTOISE_CONF = {
    "connections": {"default": "sqlite://:memory:"},
    "apps": {
        "models": {
            "models": ["goosebit.models", "aerich.models"],
        },
    },
}


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clear_cache():
    await caches.get("default").clear()
    yield


@pytest_asyncio.fixture(scope="module")
async def test_app():
    async with RegisterTortoise(
        app=app,
        config=TORTOISE_CONF,
    ):
        yield app


@pytest_asyncio.fixture(scope="module")
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
    from goosebit.models import Device, Hardware, Rollout, Software

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        compatibility = await Hardware.create(model="default", revision="default")

        device_rollout = await Device.create(
            uuid="device1",
            last_state=UpdateStateEnum.REGISTERED,
            update_mode=UpdateModeEnum.ROLLOUT,
            hardware=compatibility,
        )

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
        await software_beta.compatibility.add(compatibility)

        software_release = await Software.create(
            version="1.0.0",
            hash="dummy",
            size=1200,
            uri=uri,
        )
        await software_release.compatibility.add(compatibility)

        software_rc = await Software.create(
            version="1.0.0-rc2+build77",
            hash="dummy2",
            size=800,
            uri=uri,
        )
        await software_rc.compatibility.add(compatibility)

        rollout_default = await Rollout.create(software_id=software_release.id)

        yield dict(
            device_rollout=device_rollout,
            software_release=software_release,
            software_rc=software_rc,
            software_beta=software_beta,
            rollout_default=rollout_default,
        )
