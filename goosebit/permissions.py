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


class TunnelPermissions(PermissionsBase):
    READ = "tunnels.read"
    WRITE = "tunnels.write"
    DELETE = "tunnels.delete"


class HomePermissions(PermissionsBase):
    READ = "home.read"


class Permissions:
    HOME = HomePermissions
    FIRMWARE = FirmwarePermissions
    DEVICE = DevicePermissions
    TUNNEL = TunnelPermissions

    @classmethod
    def full(cls):
        all_items = set()
        for item in [cls.HOME, cls.FIRMWARE, cls.DEVICE, cls.TUNNEL]:
            all_items.update(item.full())
        return list(all_items)


ADMIN = Permissions.full()
MONITORING = [
    *Permissions.HOME.full(),
    *Permissions.FIRMWARE.full(),
    *Permissions.DEVICE.full(),
]
READONLY = [Permissions.HOME.READ]
