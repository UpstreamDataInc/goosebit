from enum import IntEnum
from pathlib import Path
from typing import Self
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

import semver
from tortoise import Model, fields

from goosebit.api.telemetry.metrics import devices_count


class UpdateModeEnum(IntEnum):
    NONE = 0
    LATEST = 1
    PINNED = 2
    ROLLOUT = 3
    ASSIGNED = 4

    def __str__(self):
        return self.name.capitalize()

    @classmethod
    def from_str(cls, name):
        try:
            return cls[name.upper()]
        except KeyError:
            return cls.NONE


class UpdateStateEnum(IntEnum):
    NONE = 0
    UNKNOWN = 1
    REGISTERED = 2
    RUNNING = 3
    ERROR = 4
    FINISHED = 5

    def __str__(self):
        return self.name.capitalize()

    @classmethod
    def from_str(cls, name):
        try:
            return cls[name.upper()]
        except KeyError:
            return cls.NONE


class Tag(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)


class Device(Model):
    uuid = fields.CharField(max_length=255, primary_key=True)
    name = fields.CharField(max_length=255, null=True)
    assigned_software = fields.ForeignKeyField(
        "models.Software", related_name="assigned_devices", null=True, on_delete=fields.SET_NULL
    )
    force_update = fields.BooleanField(default=False)
    sw_version = fields.CharField(max_length=255, null=True)
    hardware = fields.ForeignKeyField("models.Hardware", related_name="devices")
    feed = fields.CharField(max_length=255, default="default")
    update_mode = fields.IntEnumField(UpdateModeEnum, default=UpdateModeEnum.ROLLOUT)
    last_state = fields.IntEnumField(UpdateStateEnum, default=UpdateStateEnum.UNKNOWN)
    progress = fields.IntField(null=True)
    log_complete = fields.BooleanField(default=False)
    last_log = fields.TextField(null=True)
    last_seen = fields.BigIntField(null=True)
    last_ip = fields.CharField(max_length=15, null=True)
    last_ipv6 = fields.CharField(max_length=40, null=True)
    tags = fields.ManyToManyField("models.Tag", related_name="devices", through="device_tags")

    async def save(self, *args, **kwargs):
        is_new = self._saved_in_db is False
        await super().save(*args, **kwargs)
        if is_new:
            await self.notify_created()

    async def delete(self, *args, **kwargs):
        await super().delete(*args, **kwargs)
        await self.notify_deleted()

    @staticmethod
    async def notify_created():
        devices_count.set(await Device.all().count())

    @staticmethod
    async def notify_deleted():
        devices_count.set(await Device.all().count())


class Rollout(Model):
    id = fields.IntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    name = fields.CharField(max_length=255, null=True)
    feed = fields.CharField(max_length=255, default="default")
    software = fields.ForeignKeyField("models.Software", related_name="rollouts")
    paused = fields.BooleanField(default=False)
    success_count = fields.IntField(default=0)
    failure_count = fields.IntField(default=0)


class Hardware(Model):
    id = fields.IntField(primary_key=True)
    model = fields.CharField(max_length=255)
    revision = fields.CharField(max_length=255)


class Software(Model):
    id = fields.IntField(primary_key=True)
    uri = fields.CharField(max_length=255)
    size = fields.BigIntField()
    hash = fields.CharField(max_length=255)
    version = fields.CharField(max_length=255)
    compatibility = fields.ManyToManyField(
        "models.Hardware",
        related_name="softwares",
        through="software_compatibility",
    )

    @classmethod
    async def latest(cls, device: Device) -> Self | None:
        updates = await cls.filter(compatibility__devices__uuid=device.uuid)
        if len(updates) == 0:
            return None
        return sorted(
            updates,
            key=lambda x: semver.Version.parse(x.version),
            reverse=True,
        )[0]

    @property
    def path(self):
        return Path(url2pathname(unquote(urlparse(self.uri).path)))

    @property
    def local(self) -> bool:
        return urlparse(self.uri).scheme == "file"

    @property
    def path_user(self) -> str:
        if self.local:
            return self.path.name
        else:
            return self.uri
