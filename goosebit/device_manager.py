from __future__ import annotations

import asyncio
import re
from enum import StrEnum
from typing import Any, Awaitable, Callable, Optional

from aiocache import caches
from fastapi.requests import Request

from goosebit.db.models import (
    Device,
    Hardware,
    Rollout,
    Software,
    UpdateModeEnum,
    UpdateStateEnum,
)
from goosebit.schema.updates import UpdateChunk

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

    _update_sources: list[Callable[[Request, Device], Awaitable[tuple[HandlingType, UpdateChunk | None]]]] = []
    _config_callbacks: list[Callable[[Device, dict[str, Any]], Awaitable[None]]] = []

    @staticmethod
    async def get_device(dev_id: str) -> Device:
        cache = caches.get("default")
        device = await cache.get(dev_id)
        if device:
            return device

        hardware = DeviceManager._hardware_default
        if hardware is None:
            hardware = (await Hardware.get_or_create(model="default", revision="default"))[0]
            DeviceManager._hardware_default = hardware

        device = (await Device.get_or_create(id=dev_id, defaults={"hardware": hardware}))[0]
        result = await cache.set(device.id, device, ttl=600)
        assert result, "device being cached"

        return device

    @staticmethod
    async def save_device(device: Device, update_fields: list[str]):
        await device.save(update_fields=update_fields)

        # only update cache after a successful database save
        result = await caches.get("default").set(device.id, device, ttl=600)
        assert result, "device being cached"

    @staticmethod
    async def update_auth_token(device: Device, auth_token: str) -> None:
        device.auth_token = auth_token
        await DeviceManager.save_device(device, update_fields=["auth_token"])

    @staticmethod
    async def update_force_update(device: Device, force_update: bool) -> None:
        device.force_update = force_update
        await DeviceManager.save_device(device, update_fields=["force_update"])

    @staticmethod
    async def update_sw_version(device: Device, version: str) -> None:
        device.sw_version = version
        await DeviceManager.save_device(device, update_fields=["sw_version"])

    @staticmethod
    async def update_hardware(device: Device, hardware: Hardware) -> None:
        device.hardware = hardware
        await DeviceManager.save_device(device, update_fields=["hardware"])

    @staticmethod
    async def update_device_state(device: Device, state: UpdateStateEnum) -> None:
        device.last_state = state
        await DeviceManager.save_device(device, update_fields=["last_state"])

    @staticmethod
    async def update_last_connection(device: Device, last_seen: int, last_ip: str | None = None) -> None:
        device.last_seen = last_seen
        if last_ip is None:
            await DeviceManager.save_device(device, update_fields=["last_seen"])
        elif ":" in last_ip:
            device.last_ipv6 = last_ip
            await DeviceManager.save_device(device, update_fields=["last_seen", "last_ipv6"])
        else:
            device.last_ip = last_ip
            await DeviceManager.save_device(device, update_fields=["last_seen", "last_ip"])

    @staticmethod
    async def update_update(device: Device, update_mode: UpdateModeEnum, software: Software | None):
        device.assigned_software = software
        device.update_mode = update_mode
        if not update_mode == UpdateModeEnum.ROLLOUT:
            device.feed = None
        await DeviceManager.save_device(device, update_fields=["assigned_software_id", "update_mode", "feed"])

    @staticmethod
    async def update_name(device: Device, name: str):
        device.name = name
        await DeviceManager.save_device(device, update_fields=["name"])

    @staticmethod
    async def update_feed(device: Device, feed: str):
        device.feed = feed
        await DeviceManager.save_device(device, update_fields=["feed"])

    @staticmethod
    def add_config_callback(callback: Callable[[Device, dict[str, Any]], Awaitable[None]]):
        DeviceManager._config_callbacks.append(callback)

    @staticmethod
    def remove_config_callback(callback: Callable[[Device, dict[str, Any]], Awaitable[None]]):
        DeviceManager._config_callbacks.remove(callback)

    @staticmethod
    async def update_config_data(device: Device, **kwargs: dict[str, Any]):
        model = kwargs.get("hw_boardname") or "default"
        revision = kwargs.get("hw_revision") or "default"
        sw_version = kwargs.get("sw_version")

        await asyncio.gather(
            *[cb(device, **kwargs) for cb in DeviceManager._config_callbacks]  # type: ignore[call-arg]
        )

        hardware = (await Hardware.get_or_create(model=model, revision=revision))[0]
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
            await DeviceManager.save_device(device, update_fields=["hardware_id", "last_state", "sw_version"])

    @staticmethod
    async def deployment_action_start(device: Device):
        device.last_log = ""
        device.progress = 0
        await DeviceManager.save_device(device, update_fields=["last_log", "progress"])

    @staticmethod
    async def deployment_action_success(device: Device):
        device.progress = 100
        await DeviceManager.save_device(device, update_fields=["progress"])

    @staticmethod
    async def get_rollout(device: Device) -> Rollout | None:
        if device.update_mode == UpdateModeEnum.ROLLOUT:
            return (
                await Rollout.filter(
                    feed=device.feed,
                    paused=False,
                    software__compatibility__devices__id=device.id,
                )
                .order_by("-created_at")
                .first()
                .prefetch_related("software")
            )

        return None

    @staticmethod
    async def _get_software(device: Device) -> Software | None:
        if device.update_mode == UpdateModeEnum.ROLLOUT:
            rollout = await DeviceManager.get_rollout(device)
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

    @staticmethod
    def add_update_source(source: Callable[[Request, Device], Awaitable[tuple[HandlingType, UpdateChunk | None]]]):
        DeviceManager._update_sources.append(source)

    @staticmethod
    async def get_alt_src_updates(request: Request, device: Device) -> list[tuple[HandlingType, UpdateChunk | None]]:
        return await asyncio.gather(*[source(request, device) for source in DeviceManager._update_sources])

    @staticmethod
    async def get_update(device: Device) -> tuple[HandlingType, Software | None]:
        software = await DeviceManager._get_software(device)

        if software is None:
            handling_type = HandlingType.SKIP

        elif software.version == device.sw_version and not device.force_update:
            handling_type = HandlingType.SKIP

        elif device.last_state == UpdateStateEnum.ERROR and not device.force_update:
            handling_type = HandlingType.SKIP

        else:
            handling_type = HandlingType.FORCED

        return handling_type, software

    @staticmethod
    async def update_log(device: Device, log_data: str) -> None:
        if log_data is None:
            return

        if device.last_log is None:
            device.last_log = ""

        # SWUpdate-specific log parsing to report progress
        matches = re.findall(r"Downloaded (\d+)%", log_data)
        if matches:
            device.progress = matches[-1]

        device.last_log += f"{log_data}\n"

        await DeviceManager.save_device(device, update_fields=["progress", "last_log"])

    @staticmethod
    async def delete_devices(ids: list[str]):
        await Device.filter(id__in=ids).delete()
        for dev_id in ids:
            result = await caches.get("default").delete(dev_id)
            assert result == 1, "device has been cached"


async def get_device(dev_id: str) -> Device:
    return await DeviceManager.get_device(dev_id)


async def get_device_or_none(dev_id: str) -> Optional[Device]:
    return await Device.get_or_none(id=dev_id)
