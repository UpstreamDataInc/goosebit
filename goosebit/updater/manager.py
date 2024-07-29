from __future__ import annotations

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from enum import StrEnum
from typing import Callable, Optional

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


class HandlingType(StrEnum):
    SKIP = "skip"
    ATTEMPT = "attempt"
    FORCED = "forced"


class UpdateManager(ABC):
    def __init__(self, dev_id: str):
        self.dev_id = dev_id

    async def get_device(self) -> Device | None:
        return

    async def update_force_update(self, force_update: bool) -> None:
        return

    async def update_fw_version(self, version: str) -> None:
        return

    async def update_hardware(self, hardware: Hardware) -> None:
        return

    async def update_device_state(self, state: UpdateStateEnum) -> None:
        return

    async def update_last_connection(self, last_seen: int, last_ip: str) -> None:
        return

    async def update_update(
        self, update_mode: UpdateModeEnum, firmware: Firmware | None
    ):
        return

    async def update_name(self, name: str):
        return

    async def update_config_data(self, **kwargs):
        return

    async def get_rollout(self) -> Optional[Rollout]:
        return None

    @asynccontextmanager
    async def subscribe_log(self, callback: Callable):
        device = await self.get_device()
        subscribers = self.log_subscribers
        subscribers.append(callback)
        self.log_subscribers = subscribers
        await callback(device.last_log)
        try:
            yield
        except asyncio.CancelledError:
            pass
        finally:
            subscribers = self.log_subscribers
            subscribers.remove(callback)
            self.log_subscribers = subscribers

    @property
    def poll_seconds(self):
        time_obj = datetime.strptime(self.poll_time, "%H:%M:%S")
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

    @property
    def log_subscribers(self):
        return device_log_subscriptions.get(self.dev_id, [])

    @log_subscribers.setter
    def log_subscribers(self, value: list):
        device_log_subscriptions[self.dev_id] = value

    @property
    def update_complete(self):
        return device_update_status.get(self.dev_id, False)

    @update_complete.setter
    def update_complete(self, value: bool):
        device_update_status[self.dev_id] = value

    @property
    def poll_time(self):
        return device_poll_time.get(self.dev_id, POLL_TIME)

    @poll_time.setter
    def poll_time(self, value: str):
        device_poll_time[self.dev_id] = value

    async def publish_log(self, log_data: str | None):
        for cb in self.log_subscribers:
            await cb(log_data)

    @abstractmethod
    async def get_update(self) -> tuple[HandlingType, Firmware]: ...

    @abstractmethod
    async def update_log(self, log_data: str) -> None: ...


class UnknownUpdateManager(UpdateManager):
    def __init__(self, dev_id: str):
        super().__init__(dev_id)
        self.poll_time = POLL_TIME_UPDATING

    async def _get_firmware(self) -> Firmware:
        return await Firmware.latest(await self.get_device())

    async def get_update(self) -> tuple[HandlingType, Firmware]:
        firmware = await self._get_firmware()
        return HandlingType.FORCED, firmware

    async def update_log(self, log_data: str) -> None:
        return


class DeviceUpdateManager(UpdateManager):
    async def get_device(self) -> Device:
        hardware = (await Hardware.get_or_create(model="default", revision="default"))[
            0
        ]
        return (
            await Device.get_or_create(
                uuid=self.dev_id, defaults={"hardware": hardware}
            )
        )[0]

    async def update_force_update(self, force_update: bool) -> None:
        device = await self.get_device()
        device.force_update = force_update
        await device.save(update_fields=["force_update"])

    async def update_fw_version(self, version: str) -> None:
        device = await self.get_device()
        device.fw_version = version
        await device.save(update_fields=["fw_version"])

    async def update_hardware(self, hardware: Hardware) -> None:
        device = await self.get_device()
        device.hardware = hardware
        await device.save(update_fields=["hardware"])

    async def update_device_state(self, state: UpdateStateEnum) -> None:
        device = await self.get_device()
        device.last_state = state
        await device.save(update_fields=["last_state"])

    async def update_last_connection(self, last_seen: int, last_ip: str) -> None:
        device = await self.get_device()
        device.last_seen = last_seen
        if ":" in last_ip:
            device.last_ipv6 = last_ip
            await device.save(update_fields=["last_seen", "last_ipv6"])
        else:
            device.last_ip = last_ip
            await device.save(update_fields=["last_seen", "last_ip"])

    async def update_update(
        self, update_mode: UpdateModeEnum, firmware: Firmware | None
    ):
        device = await self.get_device()
        device.assigned_firmware = firmware
        device.update_mode = update_mode
        await device.save(update_fields=["assigned_firmware_id", "update_mode"])

    async def update_name(self, name: str):
        device = await self.get_device()
        device.name = name
        await device.save(update_fields=["name"])

    async def update_config_data(self, **kwargs):
        model = kwargs.get("hw_model") or "default"
        revision = kwargs.get("hw_revision") or "default"
        hardware = (await Hardware.get_or_create(model=model, revision=revision))[0]
        device = await self.get_device()
        modified = False

        if device.hardware != hardware:
            device.hardware = hardware
            modified = True

        if device.last_state == UpdateStateEnum.UNKNOWN:
            device.last_state = UpdateStateEnum.REGISTERED
            modified = True

        if modified:
            await device.save(update_fields=["hardware_id", "last_state"])

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

    async def get_update(self) -> tuple[HandlingType, Firmware]:
        device = await self.get_device()
        firmware = await self._get_firmware()

        if firmware is None:
            handling_type = HandlingType.SKIP
            self.poll_time = POLL_TIME

        elif firmware.version == device.fw_version and not device.force_update:
            handling_type = HandlingType.SKIP
            self.poll_time = POLL_TIME

        elif device.last_state == UpdateStateEnum.ERROR and not device.force_update:
            handling_type = HandlingType.SKIP
            self.poll_time = POLL_TIME

        else:
            handling_type = HandlingType.FORCED
            self.poll_time = POLL_TIME_UPDATING

            if self.update_complete:
                self.update_complete = False
                await self.clear_log()

        return handling_type, firmware

    async def update_log(self, log_data: str) -> None:
        if log_data is None:
            return
        device = await self.get_device()

        if device.last_log is None:
            device.last_log = ""

        matches = re.findall(r"Downloaded (\d+)%", log_data)
        if matches:
            device.progress = matches[-1]

        if log_data.startswith("Installing Update Chunk Artifacts."):
            # clear log
            device.last_log = ""
            await self.publish_log(None)
        elif log_data == "All Chunks Installed.":
            device.force_update = False
            self.update_complete = True

        if not log_data == "Skipped Update.":
            device.last_log += f"{log_data}\n"
            await self.publish_log(f"{log_data}\n")

        await device.save(update_fields=["progress", "last_log", "force_update"])

    async def clear_log(self) -> None:
        device = await self.get_device()
        device.last_log = ""
        await device.save(update_fields=["last_log"])
        await self.publish_log(None)


device_log_subscriptions: dict[str, list[Callable]] = {}
device_update_status: dict[str, bool] = {}
device_poll_time: dict[str, str] = {}
device_managers = {"unknown": UnknownUpdateManager("unknown")}


async def get_update_manager(dev_id: str) -> UpdateManager:
    global device_managers
    if device_managers.get(dev_id) is not None:
        return device_managers[dev_id]
    manager = DeviceUpdateManager(dev_id)
    devices_count.set(await Device.all().count())
    return manager


async def delete_device(dev_id: str) -> None:
    global device_managers
    try:
        updater = await get_update_manager(dev_id)
        await (await updater.get_device()).delete()
        del device_managers[dev_id]
    except KeyError as e:
        logging.warning(f"Deleting device failed, error={e}, device={dev_id}")


def reset_update_manager():
    global device_managers
    device_managers = {"unknown": UnknownUpdateManager("unknown")}
