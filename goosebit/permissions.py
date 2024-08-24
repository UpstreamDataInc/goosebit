from enum import Enum
from typing import ClassVar, TypeVar, cast

from pydantic import BaseModel

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


class SoftwarePermissions(PermissionsBase):
    READ = "software.read"
    WRITE = "software.write"
    DELETE = "software.delete"


class DevicePermissions(PermissionsBase):
    READ = "device.read"
    WRITE = "device.write"
    DELETE = "device.delete"


class RolloutPermissions(PermissionsBase):
    READ = "rollout.read"
    WRITE = "rollout.write"
    DELETE = "rollout.delete"


class HomePermissions(PermissionsBase):
    READ = "home.read"


class Permissions(BaseModel):
    HOME: ClassVar = HomePermissions
    SOFTWARE: ClassVar = SoftwarePermissions
    DEVICE: ClassVar = DevicePermissions
    ROLLOUT: ClassVar = RolloutPermissions

    @classmethod
    def full(cls) -> set[T]:
        all_items = set()
        for item in [cls.HOME, cls.SOFTWARE, cls.DEVICE, cls.ROLLOUT]:
            all_items.update(item.full())
        return all_items

    @classmethod
    def from_str(cls, permission: str) -> set[T]:
        if permission == "*":
            return cls.full()
        area, action = permission.upper().split(".")
        if area == "SOFTWARE":
            return {SoftwarePermissions[action]}
        if area == "DEVICE":
            return {DevicePermissions[action]}
        if area == "ROLLOUT":
            return {RolloutPermissions[action]}
        if area == "HOME":
            return {HomePermissions[action]}


ADMIN = Permissions.full()
MONITORING = [
    *Permissions.HOME.full(),
    *Permissions.SOFTWARE.full(),
    *Permissions.DEVICE.full(),
]
READONLY = [Permissions.HOME.READ]
