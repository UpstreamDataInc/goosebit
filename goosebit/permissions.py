from enum import Enum


class PermissionsBase(str, Enum):
    @classmethod
    def full(cls) -> list:
        return [i for i in cls]

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


class HomePermissions(PermissionsBase):
    READ = "home.read"


class Permissions:
    HOME = HomePermissions
    FIRMWARE = FirmwarePermissions
    DEVICE = DevicePermissions

    @classmethod
    def full(cls):
        all_items = set()
        for item in [cls.HOME, cls.FIRMWARE, cls.DEVICE]:
            all_items.update(item.full())
        return list(all_items)

    @classmethod
    def from_str(cls, permission: str):
        if permission == "*":
            return cls.full()
        permission_type = permission.split(".")[0]
        if permission_type == "firmware":
            return FirmwarePermissions(permission)
        if permission_type == "devices":
            return FirmwarePermissions(permission)
        if permission_type == "home":
            return FirmwarePermissions(permission)


ADMIN = Permissions.full()
MONITORING = [
    *Permissions.HOME.full(),
    *Permissions.FIRMWARE.full(),
    *Permissions.DEVICE.full(),
]
READONLY = [Permissions.HOME.READ]
