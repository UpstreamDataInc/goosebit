from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from enum import StrEnum
from typing import Callable

from aiocache import cached, caches

from goosebit.db.models import (
    Device,
    Hardware,
    Rollout,
    Software,
    UpdateModeEnum,
    UpdateStateEnum,
)
from goosebit.settings import config

caches.set_config(
    {
        "default": {
            "cache": "aiocache.SimpleMemoryCache",
            "serializer": {"class": "aiocache.serializers.PickleSerializer"},
            "ttl": 600,
        },
    }
)


class HandlingType(StrEnum):
    SKIP = "skip"
    ATTEMPT = "attempt"
    FORCED = "forced"


class UpdateManager(ABC):
    device_log_subscriptions: dict[str, list[Callable]] = {}
    device_poll_time: dict[str, str] = {}

    def __init__(self, dev_id: str):
        self.dev_id = dev_id

    async def get_device(self) -> Device | None:
        return

    async def update_force_update(self, force_update: bool) -> None:
        return

    async def update_sw_version(self, version: str) -> None:
        return

    async def update_hardware(self, hardware: Hardware) -> None:
        return

    async def update_device_state(self, state: UpdateStateEnum) -> None:
        return

    async def update_last_connection(self, last_seen: int, last_ip: str) -> None:
        return

    async def update_update(self, update_mode: UpdateModeEnum, software: Software | None):
        return

    async def update_name(self, name: str):
        return

    async def update_feed(self, feed: str):
        return

    async def update_config_data(self, **kwargs):
        return

    async def update_log_complete(self, log_complete: bool):
        return

    async def get_rollout(self) -> Rollout | None:
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
        return UpdateManager.device_log_subscriptions.get(self.dev_id, [])

    @log_subscribers.setter
    def log_subscribers(self, value: list):
        UpdateManager.device_log_subscriptions[self.dev_id] = value

    @property
    def poll_time(self):
        return UpdateManager.device_poll_time.get(self.dev_id, config.poll_time_default)

    @poll_time.setter
    def poll_time(self, value: str):
        if not value == config.poll_time_default:
            UpdateManager.device_poll_time[self.dev_id] = value
            return
        if self.dev_id in UpdateManager.device_poll_time:
            del UpdateManager.device_poll_time[self.dev_id]

    async def publish_log(self, log_data: str | None):
        for cb in self.log_subscribers:
            await cb(log_data)

    @abstractmethod
    async def get_update(self) -> tuple[HandlingType, Software]: ...

    @abstractmethod
    async def update_log(self, log_data: str) -> None: ...


class UnknownUpdateManager(UpdateManager):
    def __init__(self, dev_id: str):
        super().__init__(dev_id)
        self.poll_time = config.poll_time_updating

    async def _get_software(self) -> Software:
        return await Software.latest(await self.get_device())

    async def get_update(self) -> tuple[HandlingType, Software]:
        software = await self._get_software()
        return HandlingType.FORCED, software

    async def update_log(self, log_data: str) -> None:
        return


class DeviceUpdateManager(UpdateManager):
    hardware_default = None

    @cached(key_builder=lambda fn, self: self.dev_id, alias="default")
    async def get_device(self) -> Device:
        hardware = DeviceUpdateManager.hardware_default
        if hardware is None:
            hardware = (await Hardware.get_or_create(model="default", revision="default"))[0]
            DeviceUpdateManager.hardware_default = hardware

        return (await Device.get_or_create(uuid=self.dev_id, defaults={"hardware": hardware}))[0]

    async def save_device(self, device: Device, update_fields: list[str]):
        result = await caches.get("default").set(self.dev_id, device, ttl=600)
        assert result, "device being cached"
        await device.save(update_fields=update_fields)

    async def update_force_update(self, force_update: bool) -> None:
        device = await self.get_device()
        device.force_update = force_update
        await self.save_device(device, update_fields=["force_update"])

    async def update_sw_version(self, version: str) -> None:
        device = await self.get_device()
        device.sw_version = version
        await self.save_device(device, update_fields=["sw_version"])

    async def update_hardware(self, hardware: Hardware) -> None:
        device = await self.get_device()
        device.hardware = hardware
        await self.save_device(device, update_fields=["hardware"])

    async def update_device_state(self, state: UpdateStateEnum) -> None:
        device = await self.get_device()
        device.last_state = state
        await self.save_device(device, update_fields=["last_state"])

    async def update_last_connection(self, last_seen: int, last_ip: str) -> None:
        device = await self.get_device()
        device.last_seen = last_seen
        if ":" in last_ip:
            device.last_ipv6 = last_ip
            await self.save_device(device, update_fields=["last_seen", "last_ipv6"])
        else:
            device.last_ip = last_ip
            await self.save_device(device, update_fields=["last_seen", "last_ip"])

    async def update_update(self, update_mode: UpdateModeEnum, software: Software | None):
        device = await self.get_device()
        device.assigned_software = software
        device.update_mode = update_mode
        await self.save_device(device, update_fields=["assigned_software_id", "update_mode"])

    async def update_name(self, name: str):
        device = await self.get_device()
        device.name = name
        await self.save_device(device, update_fields=["name"])

    async def update_feed(self, feed: str):
        device = await self.get_device()
        device.feed = feed
        await self.save_device(device, update_fields=["feed"])

    async def update_config_data(self, **kwargs):
        model = kwargs.get("hw_boardname") or "default"
        revision = kwargs.get("hw_revision") or "default"
        sw_version = kwargs.get("sw_version")

        hardware = (await Hardware.get_or_create(model=model, revision=revision))[0]
        device = await self.get_device()
        modified = False

        if device.hardware != hardware:
            device.hardware = hardware
            modified = True

        if device.last_state == UpdateStateEnum.UNKNOWN:
            device.last_state = UpdateStateEnum.REGISTERED
            modified = True

        if device.sw_version != sw_version:
            device.sw_version = sw_version
            modified = True

        if modified:
            await self.save_device(device, update_fields=["hardware_id", "last_state", "sw_version"])

    async def update_log_complete(self, log_complete: bool):
        device = await self.get_device()
        device.log_complete = log_complete
        await self.save_device(device, update_fields=["log_complete"])

    async def get_rollout(self) -> Rollout | None:
        device = await self.get_device()

        if device.update_mode == UpdateModeEnum.ROLLOUT:
            return (
                await Rollout.filter(
                    feed=device.feed,
                    paused=False,
                    software__compatibility__devices__uuid=device.uuid,
                )
                .order_by("-created_at")
                .first()
                .prefetch_related("software")
            )

        return None

    async def _get_software(self) -> Software | None:
        device = await self.get_device()

        if device.update_mode == UpdateModeEnum.ROLLOUT:
            rollout = await self.get_rollout()
            if not rollout or rollout.paused:
                return None
            await rollout.fetch_related("software")
            return rollout.software
        if device.update_mode == UpdateModeEnum.ASSIGNED:
            await device.fetch_related("assigned_software")
            return device.assigned_software

        if device.update_mode == UpdateModeEnum.LATEST:
            return await Software.latest(device)

        assert device.update_mode == UpdateModeEnum.PINNED
        return None

    async def get_update(self) -> tuple[HandlingType, Software]:
        device = await self.get_device()
        software = await self._get_software()

        if software is None:
            handling_type = HandlingType.SKIP
            self.poll_time = config.poll_time_default

        elif software.version == device.sw_version and not device.force_update:
            handling_type = HandlingType.SKIP
            self.poll_time = config.poll_time_default

        elif device.last_state == UpdateStateEnum.ERROR and not device.force_update:
            handling_type = HandlingType.SKIP
            self.poll_time = config.poll_time_default

        else:
            handling_type = HandlingType.FORCED
            self.poll_time = config.poll_time_updating

            if device.log_complete:
                await self.update_log_complete(False)
                await self.clear_log()

        return handling_type, software

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

        if not log_data == "Skipped Update.":
            device.last_log += f"{log_data}\n"
            await self.publish_log(f"{log_data}\n")

        await self.save_device(
            device,
            update_fields=["progress", "last_log"],
        )

    async def clear_log(self) -> None:
        device = await self.get_device()
        device.last_log = ""
        await self.save_device(device, update_fields=["last_log"])
        await self.publish_log(None)


async def get_update_manager(dev_id: str) -> UpdateManager:
    if dev_id == "unknown":
        return UnknownUpdateManager("unknown")
    else:
        return DeviceUpdateManager(dev_id)


async def delete_devices(ids: list[str]):
    await Device.filter(uuid__in=ids).delete()
    for dev_id in ids:
        result = await caches.get("default").delete(dev_id)
        assert result == 1, "device has been cached"
