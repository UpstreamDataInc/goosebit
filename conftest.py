import logging
import os
import tempfile
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise
from tortoise.contrib.fastapi import RegisterTortoise

from goosebit import app
from goosebit.models import UpdateModeEnum
from goosebit.updater.manager import reset_update_manager

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
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def db():
    reset_update_manager()

    await Tortoise.init(config=TORTOISE_CONF)
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()
    await Tortoise.close_connections()


@pytest_asyncio.fixture(scope="function")
async def test_data(db):
    from goosebit.models import Device, Firmware, Hardware, Rollout

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        compatibility = await Hardware.create(model="default", revision="default")

        device_rollout = await Device.create(
            uuid="device1",
            last_state="registered",
            update_mode=UpdateModeEnum.ROLLOUT,
            hardware=compatibility,
        )

        device_latest = await Device.create(
            uuid="device2",
            last_state="registered",
            update_mode=UpdateModeEnum.LATEST,
            hardware=compatibility,
        )

        device_pinned = await Device.create(
            uuid="device3",
            last_state="registered",
            update_mode=UpdateModeEnum.PINNED,
            hardware=compatibility,
        )

        temp_file_path = os.path.join(temp_dir, "firmware")
        with open(temp_file_path, "w") as temp_file:
            temp_file.write("Fake SWUpdate image")
        uri = Path(temp_file_path).as_uri()

        firmware_beta = await Firmware.create(
            version="1.0.0-beta2+build20",
            hash="dummy2",
            size=800,
            uri=uri,
        )
        await firmware_beta.compatibility.add(compatibility)

        firmware_latest = await Firmware.create(
            version="1.0.0",
            hash="dummy",
            size=1200,
            uri=uri,
        )
        await firmware_latest.compatibility.add(compatibility)

        firmware_rc = await Firmware.create(
            version="1.0.0-rc2+build77",
            hash="dummy2",
            size=800,
            uri=uri,
        )
        await firmware_rc.compatibility.add(compatibility)

        rollout_default = await Rollout.create(firmware_id=firmware_latest.id)

        yield dict(
            device_rollout=device_rollout,
            device_latest=device_latest,
            device_pinned=device_pinned,
            firmware_latest=firmware_latest,
            rollout_default=rollout_default,
        )