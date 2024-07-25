import logging
import os
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient
from tortoise import Tortoise
from tortoise.contrib.fastapi import RegisterTortoise

from goosebit import app

# Configure logging
logging.basicConfig(level=logging.INFO)

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
        generate_schemas=True,
        add_exception_handlers=True,
        _create_db=True,
    ):
        yield app


@pytest_asyncio.fixture(scope="module")
async def async_client(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def db():
    await Tortoise.init(config=TORTOISE_CONF)
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()
    await Tortoise.close_connections()


@pytest_asyncio.fixture(scope="function")
async def test_data(db, monkeypatch):
    # Initialize the data
    from goosebit.models import (  # Import your models here
        Device,
        FirmwareCompatibility,
        FirmwareUpdate,
        Rollout,
    )

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        device_none = await Device.create(
            uuid="device1", last_state="registered", fw_file="none"
        )

        device_latest = await Device.create(
            uuid="device2", last_state="registered", fw_file="latest"
        )

        device_pinned = await Device.create(
            uuid="device3", last_state="registered", fw_file="pinned"
        )

        compatibility = await FirmwareCompatibility.create(
            hw_model="default", hw_revision="default"
        )

        temp_file_path = os.path.join(temp_dir, "firmware")
        with open(temp_file_path, "w") as temp_file:
            temp_file.write("Fake SWUpdate image")
        uri = Path(temp_file_path).as_uri()

        firmware_beta = await FirmwareUpdate.create(
            version="1.0.0-beta2+build20",
            hash="dummy2",
            size=800,
            uri=uri,
            compatibility_id=compatibility.id,
        )
        await firmware_beta.compatibility.add(compatibility)

        firmware_latest = await FirmwareUpdate.create(
            version="1.0.0",
            hash="dummy",
            size=1200,
            uri=uri,
            compatibility_id=compatibility.id,
        )
        await firmware_latest.compatibility.add(compatibility)

        firmware_rc = await FirmwareUpdate.create(
            version="1.0.0-rc2+build77",
            hash="dummy2",
            size=800,
            uri=uri,
            compatibility_id=compatibility.id,
        )
        await firmware_rc.compatibility.add(compatibility)

        rollout_default = await Rollout.create(firmware_id=firmware_latest.id)

        yield dict(
            device_none=device_none,
            device_latest=device_latest,
            device_pinned=device_pinned,
            firmware_latest=firmware_latest,
            rollout_default=rollout_default,
        )
