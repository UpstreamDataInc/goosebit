from enum import IntEnum
from pathlib import Path
from typing import Self
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

import semver
from tortoise import Model, fields


class UpdateModeEnum(IntEnum):
    LATEST = 1
    PINNED = 2
    ROLLOUT = 3
    ASSIGNED = 4

    def __str__(self):
        if self == UpdateModeEnum.LATEST:
            return "Latest"
        elif self == UpdateModeEnum.PINNED:
            return "Pinned"
        elif self == UpdateModeEnum.ROLLOUT:
            return "Rollout"
        elif self == UpdateModeEnum.ASSIGNED:
            return "Assigned"


class UpdateStateEnum(IntEnum):
    UNKNOWN = 1
    REGISTERED = 2
    RUNNING = 3
    ERROR = 4
    FINISHED = 5

    def __str__(self):
        if self == UpdateStateEnum.UNKNOWN:
            return "Unknown"
        elif self == UpdateStateEnum.REGISTERED:
            return "Registered"
        elif self == UpdateStateEnum.RUNNING:
            return "Running"
        elif self == UpdateStateEnum.ERROR:
            return "Error"
        elif self == UpdateStateEnum.FINISHED:
            return "Finished"


class Tag(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)


class Device(Model):
    uuid = fields.CharField(max_length=255, primary_key=True)
    name = fields.CharField(max_length=255, null=True)
    assigned_firmware = fields.ForeignKeyField(
        "models.Firmware", related_name="assigned_devices", null=True
    )
    fw_version = fields.CharField(max_length=255, null=True)
    hardware = fields.ForeignKeyField("models.Hardware", related_name="devices")
    feed = fields.CharField(max_length=255, default="default")
    flavor = fields.CharField(max_length=255, default="default")
    update_mode = fields.IntEnumField(UpdateModeEnum, default=UpdateModeEnum.ROLLOUT)
    last_state = fields.IntEnumField(UpdateStateEnum, default=UpdateStateEnum.UNKNOWN)
    progress = fields.IntField(null=True)
    last_log = fields.TextField(null=True)
    last_seen = fields.BigIntField(null=True)
    last_ip = fields.CharField(max_length=15, null=True)
    last_ipv6 = fields.CharField(max_length=40, null=True)
    tags = fields.ManyToManyField(
        "models.Tag", related_name="devices", through="device_tags"
    )


class Rollout(Model):
    id = fields.IntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    name = fields.CharField(max_length=255, null=True)
    feed = fields.CharField(max_length=255, default="default")
    flavor = fields.CharField(max_length=255, default="default")
    firmware = fields.ForeignKeyField("models.Firmware", related_name="rollouts")
    paused = fields.BooleanField(default=False)
    success_count = fields.IntField(default=0)
    failure_count = fields.IntField(default=0)


class Hardware(Model):
    id = fields.IntField(primary_key=True)
    model = fields.CharField(max_length=255)
    revision = fields.CharField(max_length=255)


class Firmware(Model):
    id = fields.IntField(primary_key=True)
    uri = fields.CharField(max_length=255)
    size = fields.BigIntField()
    hash = fields.CharField(max_length=255)
    version = fields.CharField(max_length=255)
    compatibility = fields.ManyToManyField(
        "models.Hardware",
        related_name="firmwares",
        through="firmware_compatibility",
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
    def local(self):
        return urlparse(self.uri).scheme == "file"
