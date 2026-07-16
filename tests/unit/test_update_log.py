import pytest

from goosebit.db.models import Device
from goosebit.device_manager import DeviceManager


@pytest.mark.asyncio
async def test_update_log_appends_from_null(db: None) -> None:
    device = await DeviceManager.get_device("log-append-device")
    assert device.last_log is None

    await DeviceManager.update_log(device, "line1")
    # passed-in object is refreshed
    assert device.last_log == "line1\n"
    assert (await Device.get(id="log-append-device")).last_log == "line1\n"

    await DeviceManager.update_log(device, "line2")
    assert device.last_log == "line1\nline2\n"
    assert (await Device.get(id="log-append-device")).last_log == "line1\nline2\n"


@pytest.mark.asyncio
async def test_update_log_parses_progress(db: None) -> None:
    device = await DeviceManager.get_device("log-progress-device")

    await DeviceManager.update_log(device, "Downloaded 42%")

    assert (await Device.get(id="log-progress-device")).progress == 42


@pytest.mark.asyncio
async def test_update_log_no_lost_update(db: None) -> None:
    await DeviceManager.get_device("log-race-device")

    # two independent snapshots, as two workers would hold
    device_a = await Device.get(id="log-race-device")
    device_b = await Device.get(id="log-race-device")

    await DeviceManager.update_log(device_a, "from-worker-a")
    await DeviceManager.update_log(device_b, "from-worker-b")

    last_log = (await Device.get(id="log-race-device")).last_log
    assert "from-worker-a\n" in last_log
    assert "from-worker-b\n" in last_log
