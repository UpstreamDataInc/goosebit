from __future__ import annotations

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from enum import StrEnum
from typing import Callable, Optional, Tuple

from goosebit.models import (
    Device,
    Firmware,
    Hardware,
    Rollout,
    UpdateModeEnum,
    UpdateStateEnum,
)
from goosebit.settings import POLL_TIME, POLL_TIME_UPDATING
from goosebit.telemetry import devices_count

logger = logging.getLogger(__name__)


class HandlingType(StrEnum):
    SKIP = "skip"
    ATTEMPT = "attempt"
    FORCED = "forced"


class UpdateManager(ABC):
    def __init__(self, dev_id: str):
        self.dev_id = dev_id
        self.config_data = {}
        self.device = None
        self.force_update = False
        self.update_complete = False
        self.poll_time = POLL_TIME
        self.log_subscribers: list[Callable] = []

    async def get_device(self) -> Device | None:
        return

    async def save(self) -> None:
        return

    async def update_fw_version(self, version: str) -> None:
        return

    async def update_hardware(self, hardware: Hardware) -> None:
        return

    async def update_device_state(self, state: UpdateStateEnum) -> None:
        return

    async def update_last_seen(self, last_seen: int) -> None:
        return

    async def update_last_ip(self, last_ip: str) -> None:
        return

    async def get_rollout(self) -> Optional[Rollout]:
        return None

    async def update_config_data(self, **kwargs):
        model = kwargs.get("hw_model") or "default"
        revision = kwargs.get("hw_revision") or "default"
        hardware = (await Hardware.get_or_create(model=model, revision=revision))[0]

        await self.update_hardware(hardware)

        device = await self.get_device()
        if device.last_state == UpdateStateEnum.UNKNOWN:
            await self.update_device_state(UpdateStateEnum.REGISTERED)
        await self.save()

        self.config_data.update(kwargs)

    @asynccontextmanager
    async def subscribe_log(self, callback: Callable):
        device = await self.get_device()
        self.log_subscribers.append(callback)
        await callback(device.last_log)
        try:
            yield
        except asyncio.CancelledError:
            pass
        finally:
            self.log_subscribers.remove(callback)

    @property
    def poll_seconds(self):
        time_obj = datetime.strptime(self.poll_time, "%H:%M:%S")
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

    async def publish_log(self, log_data: str | None):
        for cb in self.log_subscribers:
            await cb(log_data)

    @abstractmethod
    async def get_update(self) -> Tuple[HandlingType, Firmware]: ...

    @abstractmethod
    async def update_log(self, log_data: str) -> None: ...


class UnknownUpdateManager(UpdateManager):
    def __init__(self, dev_id: str):
        super().__init__(dev_id)
        self.poll_time = POLL_TIME_UPDATING

    async def _get_firmware(self) -> Firmware:
        return await Firmware.latest(await self.get_device())

    async def get_update(self) -> Tuple[HandlingType, Firmware]:
        firmware = await self._get_firmware()
        return HandlingType.FORCED, firmware

    async def update_log(self, log_data: str) -> None:
        return


class DeviceUpdateManager(UpdateManager):
    async def get_device(self) -> Device:
        if not self.device:
            hardware = (
                await Hardware.get_or_create(model="default", revision="default")
            )[0]
            self.device = (
                await Device.get_or_create(
                    uuid=self.dev_id, defaults={"hardware": hardware}
                )
            )[0]

        return self.device

    async def save(self) -> None:
        await self.device.save()

    async def update_fw_version(self, version: str) -> None:
        device = await self.get_device()
        device.fw_version = version

    async def update_hardware(self, hardware: Hardware) -> None:
        device = await self.get_device()
        device.hardware = hardware

    async def update_device_state(self, state: UpdateStateEnum) -> None:
        device = await self.get_device()
        device.last_state = state

    async def update_last_seen(self, last_seen: int) -> None:
        device = await self.get_device()
        device.last_seen = last_seen

    async def update_last_ip(self, last_ip: str) -> None:
        device = await self.get_device()
        if ":" in last_ip:
            device.last_ipv6 = last_ip
        else:
            device.last_ip = last_ip

    async def get_rollout(self) -> Optional[Rollout]:
        device = await self.get_device()

        if device.update_mode == UpdateModeEnum.ROLLOUT:
            return (
                await Rollout.filter(firmware__compatibility__devices__uuid=device.uuid)
                .order_by("-created_at")
                .first()
                .prefetch_related("firmware")
            )

        return None

    async def _get_firmware(self) -> Firmware | None:
        device = await self.get_device()

        if device.update_mode == UpdateModeEnum.ROLLOUT:
            rollout = await self.get_rollout()
            if not rollout or rollout.paused:
                return None
            await rollout.fetch_related("firmware")
            return rollout.firmware
        if device.update_mode == UpdateModeEnum.ASSIGNED:
            await device.fetch_related("assigned_firmware")
            return device.assigned_firmware

        if device.update_mode == UpdateModeEnum.LATEST:
            return await Firmware.latest(device)

        assert device.update_mode == UpdateModeEnum.PINNED
        return None

    async def get_update(self) -> Tuple[HandlingType, Firmware]:
        device = await self.get_device()
        firmware = await self._get_firmware()

        if firmware is None:
            handling_type = HandlingType.SKIP
            self.poll_time = POLL_TIME
            logger.info(f"Skip: no update available, device={device.uuid}")

        elif firmware.version == device.fw_version and not self.force_update:
            handling_type = HandlingType.SKIP
            self.poll_time = POLL_TIME
            logger.info(f"Skip: device up-to-date, device={device.uuid}")

        elif device.last_state == UpdateStateEnum.ERROR and not self.force_update:
            handling_type = HandlingType.SKIP
            self.poll_time = POLL_TIME
            logger.warning(f"Skip: device in error state, device={device.uuid}")

        else:
            handling_type = HandlingType.FORCED
            self.poll_time = POLL_TIME_UPDATING
            logger.info(f"Forced: update available, device={device.uuid}")

            if self.update_complete:
                self.update_complete = False
                await self.clear_log()

        return handling_type, firmware

    async def update_log(self, log_data: str) -> None:
        if log_data is None:
            return
        device = await self.get_device()
        matches = re.findall(r"Downloaded (\d+)%", log_data)
        if matches:
            device.progress = matches[-1]
        if device.last_log is None:
            device.last_log = ""
        if log_data.startswith("Installing Update Chunk Artifacts."):
            await self.clear_log()
        if log_data == "All Chunks Installed.":
            self.force_update = False
            self.update_complete = True
        if not log_data == "Skipped Update.":
            device.last_log += f"{log_data}\n"
            await self.publish_log(f"{log_data}\n")
        await device.save()

    async def clear_log(self) -> None:
        device = await self.get_device()
        device.last_log = ""
        await device.save()
        await self.publish_log(None)


device_managers = {"unknown": UnknownUpdateManager("unknown")}


async def get_update_manager(dev_id: str) -> UpdateManager:
    global device_managers
    if device_managers.get(dev_id) is None:
        device_managers[dev_id] = DeviceUpdateManager(dev_id)
    devices_count.set(await Device.all().count())
    return device_managers[dev_id]


def get_update_manager_sync(dev_id: str) -> UpdateManager:
    global device_managers
    if device_managers.get(dev_id) is None:
        device_managers[dev_id] = DeviceUpdateManager(dev_id)
    return device_managers[dev_id]


async def delete_device(dev_id: str) -> None:
    global device_managers
    try:
        updater = get_update_manager_sync(dev_id)
        await (await updater.get_device()).delete()
        del device_managers[dev_id]
    except KeyError as e:
        logging.warning(f"Deleting device failed, error={e}, device={dev_id}")


def reset_update_manager():
    global device_managers
    device_managers = {"unknown": UnknownUpdateManager("unknown")}
