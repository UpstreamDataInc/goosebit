from __future__ import annotations

import asyncio
import re
from contextlib import asynccontextmanager
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


class DeviceManager:
    _hardware_default = None
    device_log_subscriptions: dict[str, list[Callable]] = {}

    def __init__(self, dev_id: str):
        self.dev_id = dev_id

    @cached(key_builder=lambda fn, self: self.dev_id, alias="default")
    async def get_device(self) -> Device:
        hardware = DeviceManager._hardware_default
        if hardware is None:
            hardware = (await Hardware.get_or_create(model="default", revision="default"))[0]
            DeviceManager._hardware_default = hardware

        return (await Device.get_or_create(uuid=self.dev_id, defaults={"hardware": hardware}))[0]

    async def save_device(self, device: Device, update_fields: list[str]):
        await device.save(update_fields=update_fields)

        # only update cache after a successful database save
        result = await caches.get("default").set(self.dev_id, device, ttl=600)
        assert result, "device being cached"

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

    async def update_last_connection(self, last_seen: int, last_ip: str | None = None) -> None:
        device = await self.get_device()
        device.last_seen = last_seen
        if last_ip is None:
            await self.save_device(device, update_fields=["last_seen"])
        elif ":" in last_ip:
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

    async def deployment_action_start(self):
        device = await self.get_device()
        device.last_log = ""
        device.progress = 0
        await self.save_device(device, update_fields=["last_log", "progress"])

        await self.publish_log(None)

    async def deployment_action_success(self):
        device = await self.get_device()
        device.progress = 100
        await self.save_device(device, update_fields=["progress"])

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

    async def get_update(self) -> tuple[HandlingType, Software | None]:
        device = await self.get_device()
        software = await self._get_software()

        if software is None:
            handling_type = HandlingType.SKIP

        elif software.version == device.sw_version and not device.force_update:
            handling_type = HandlingType.SKIP

        elif device.last_state == UpdateStateEnum.ERROR and not device.force_update:
            handling_type = HandlingType.SKIP

        else:
            handling_type = HandlingType.FORCED

        return handling_type, software

    @asynccontextmanager
    async def subscribe_log(self, callback: Callable):
        device = await self.get_device()
        # do not modify, breaks when combined
        subscribers = self.log_subscribers
        subscribers.append(callback)
        self.log_subscribers = subscribers

        if device is not None:
            await callback(device.last_log)
        try:
            yield
        except asyncio.CancelledError:
            pass
        finally:
            # do not modify, breaks when combined
            subscribers = self.log_subscribers
            subscribers.remove(callback)
            self.log_subscribers = subscribers

    @property
    def log_subscribers(self):
        return DeviceManager.device_log_subscriptions.get(self.dev_id, [])

    @log_subscribers.setter
    def log_subscribers(self, value: list):
        DeviceManager.device_log_subscriptions[self.dev_id] = value

    async def publish_log(self, log_data: str | None):
        for cb in self.log_subscribers:
            await cb(log_data)

    async def update_log(self, log_data: str) -> None:
        if log_data is None:
            return
        device = await self.get_device()

        if device.last_log is None:
            device.last_log = ""

        # SWUpdate-specific log parsing to report progress
        matches = re.findall(r"Downloaded (\d+)%", log_data)
        if matches:
            device.progress = matches[-1]

        device.last_log += f"{log_data}\n"
        await self.publish_log(f"{log_data}\n")

        await self.save_device(device, update_fields=["progress", "last_log"])


async def get_update_manager(dev_id: str) -> DeviceManager:
    return DeviceManager(dev_id)


async def delete_devices(ids: list[str]):
    await Device.filter(uuid__in=ids).delete()
    for dev_id in ids:
        result = await caches.get("default").delete(dev_id)
        assert result == 1, "device has been cached"
