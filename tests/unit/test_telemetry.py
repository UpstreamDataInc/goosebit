import pytest

from goosebit.api.telemetry import metrics
from goosebit.db.models import Device, Hardware, User


@pytest.mark.asyncio
async def test_refresh_counts_reads_db(db: None) -> None:
    hardware = await Hardware.create(model="default", revision="default")
    await Device.create(id="device1", hardware=hardware)
    await Device.create(id="device2", hardware=hardware)
    await User.create(username="user@goosebit.test", hashed_pwd="hashed")

    await metrics.refresh_counts()

    assert metrics._devices_count == 2
    assert metrics._users_count == 1


@pytest.mark.asyncio
async def test_refresh_counts_reflects_mutations(db: None) -> None:
    hardware = await Hardware.create(model="default", revision="default")
    device = await Device.create(id="device1", hardware=hardware)

    await metrics.refresh_counts()
    assert metrics._devices_count == 1

    await device.delete()

    await metrics.refresh_counts()
    assert metrics._devices_count == 0
