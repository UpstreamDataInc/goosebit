from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Callable

import aiofiles

from goosebit.models import Device
from goosebit.settings import POLL_TIME, SWUPDATE_FILES_DIR, TOKEN_SWU_DIR
from goosebit.updater.misc import get_newest_fw
from goosebit.updater.updates import FirmwareArtifact


class UpdateManager(ABC):
    def __init__(self, dev_id: str):
        self.dev_id = dev_id
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

    async def update_device_state(self, state: str) -> None:
        return

    async def update_last_seen(self, last_seen: int) -> None:
        return

    async def update_web_pwd(self, web_pwd: str) -> None:
        return

    async def update_last_ip(self, last_ip: str) -> None:
        return

    async def update_cfd_status(self, status: bool) -> None:
        return

    async def create_cfd_token(self) -> str:
        return ""

    async def delete_cfd_token(self):
        return

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

    async def publish_log(self, log_data: str | None):
        for cb in self.log_subscribers:
            await cb(log_data)

    @property
    def cfd_provisioned(self) -> bool:
        return False

    @abstractmethod
    async def get_update_file(self) -> FirmwareArtifact: ...

    @abstractmethod
    async def get_update_mode(self) -> str: ...

    @abstractmethod
    async def update_log(self, log_data: str) -> None: ...


class UnknownUpdateManager(UpdateManager):
    def __init__(self, dev_id: str):
        super().__init__(dev_id)
        self.poll_time = "00:00:05"

    async def get_update_file(self) -> FirmwareArtifact:
        return FirmwareArtifact(get_newest_fw())

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
        file = FirmwareArtifact(device.fw_file)

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
