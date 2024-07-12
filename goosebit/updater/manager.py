from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Callable

from goosebit.models import Device
from goosebit.settings import POLL_TIME, POLL_TIME_UPDATING
from goosebit.updater.updates import FirmwareArtifact


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

    async def update_hw_model(self, hw_model: str) -> None:
        return

    async def update_hw_revision(self, hw_revision: str) -> None:
        return

    async def update_device_state(self, state: str) -> None:
        return

    async def update_last_seen(self, last_seen: int) -> None:
        return

    async def update_last_ip(self, last_ip: str) -> None:
        return

    async def update_config_data(self, **kwargs):
        await self.update_hw_model(kwargs.get("hw_model") or "default")
        await self.update_hw_revision(kwargs.get("hw_revision") or "default")
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
    async def get_update_file(self) -> FirmwareArtifact: ...

    @abstractmethod
    async def get_update_mode(self) -> str: ...

    @abstractmethod
    async def update_log(self, log_data: str) -> None: ...


class UnknownUpdateManager(UpdateManager):
    def __init__(self, dev_id: str):
        super().__init__(dev_id)
        self.poll_time = POLL_TIME_UPDATING

    async def get_update_file(self) -> FirmwareArtifact:
        return FirmwareArtifact("latest")

    async def get_update_mode(self) -> str:
        return "forced"

    async def update_log(self, log_data: str) -> None:
        return


class DeviceUpdateManager(UpdateManager):
    async def get_device(self) -> Device:
        if self.device:
            return self.device
        self.device = (await Device.get_or_create(uuid=self.dev_id))[0]
        return self.device

    async def save(self) -> None:
        await self.device.save()

    async def update_fw_version(self, version: str) -> None:
        device = await self.get_device()
        device.fw_version = version

    async def update_hw_model(self, hw_model: str) -> None:
        device = await self.get_device()
        device.hw_model = hw_model

    async def update_hw_revision(self, hw_revision: str) -> None:
        device = await self.get_device()
        device.hw_revision = hw_revision

    async def update_device_state(self, state: str) -> None:
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

    async def get_update_file(self) -> FirmwareArtifact:
        device = await self.get_device()
        file = FirmwareArtifact(device.fw_file, device.hw_model, device.hw_revision)

        if self.force_update:
            return file
        return file

    async def get_update_mode(self) -> str:
        device = await self.get_device()

        file = await self.get_update_file()
        if file.is_empty():
            mode = "skip"
            self.poll_time = POLL_TIME
        elif file.name == device.fw_version:
            mode = "skip"
            self.poll_time = POLL_TIME
        else:
            mode = "forced"
            self.poll_time = "00:00:05"

        if self.force_update:
            mode = "forced"
            self.poll_time = "00:00:05"

        if mode == "forced" and self.update_complete:
            self.update_complete = False
            await self.clear_log()

        return mode

    async def update_log(self, log_data: str) -> None:
        if log_data is None:
            return
        device = await self.get_device()
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

    async def clear_log(self) -> None:
        device = await self.get_device()
        device.last_log = ""
        await self.publish_log(None)


device_managers = {"unknown": UnknownUpdateManager("unknown")}


async def get_update_manager(dev_id: str) -> UpdateManager:
    global device_managers
    if device_managers.get(dev_id) is None:
        device_managers[dev_id] = DeviceUpdateManager(dev_id)
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
    except KeyError:
        pass
