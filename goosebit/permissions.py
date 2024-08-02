from enum import Enum
from typing import TypeVar, cast

T = TypeVar("T", bound="PermissionsBase")


class PermissionsBase(str, Enum):
    @classmethod
    def full(cls) -> set[T]:
        all_items = set[T]()
        for permission in cls:
            all_items.add(cast(T, permission))
        return all_items

    def __str__(self):
        return self.value


class FirmwarePermissions(PermissionsBase):
    READ = "firmware.read"
    WRITE = "firmware.write"
    DELETE = "firmware.delete"


class DevicePermissions(PermissionsBase):
    READ = "devices.read"
    WRITE = "devices.write"
    DELETE = "devices.delete"


class RolloutPermissions(PermissionsBase):
    READ = "rollouts.read"
    WRITE = "rollouts.write"
    DELETE = "rollouts.delete"


class HomePermissions(PermissionsBase):
    READ = "home.read"


class Permissions:
    HOME = HomePermissions
    FIRMWARE = FirmwarePermissions
    DEVICE = DevicePermissions
    ROLLOUT = RolloutPermissions

    @classmethod
    def full(cls) -> set[T]:
        all_items = set()
        for item in [cls.HOME, cls.FIRMWARE, cls.DEVICE, cls.ROLLOUT]:
            all_items.update(item.full())
        return all_items

    @classmethod
    def from_str(cls, permission: str) -> set[T]:
        if permission == "*":
            return cls.full()
        area, action = permission.upper().split(".")
        if area == "FIRMWARE":
            return {FirmwarePermissions[action]}
        if area == "DEVICES":
            return {DevicePermissions[action]}
        if area == "ROLLOUTS":
            return {RolloutPermissions[action]}
        if area == "HOME":
            return {HomePermissions[action]}


ADMIN = Permissions.full()
MONITORING = [
    *Permissions.HOME.full(),
    *Permissions.FIRMWARE.full(),
    *Permissions.DEVICE.full(),
]
READONLY = [Permissions.HOME.READ]
