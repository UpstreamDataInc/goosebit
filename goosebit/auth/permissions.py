from typing import Optional

from pydantic import BaseModel


class Permission(BaseModel):
    def model_post_init(self, ctx):
        if self.sub_permissions is None:
            return
        for permission in self.sub_permissions:
            permission.parent_permission = self

    def __call__(self, *args, **kwargs):
        if self.parent_permission is None:
            return self.name
        return ".".join([self.parent_permission(), self.name])

    def __getitem__(self, item):
        return self.sub_permissions_by_name[item]

    @property
    def sub_permissions_by_name(self) -> dict[str, "Permission"]:
        if self.sub_permissions is None:
            return {}
        return {item.name: item for item in self.sub_permissions}

    name: str
    description: str

    parent_permission: Optional["Permission"] = None
    sub_permissions: list["Permission"] | None = None


READ_PERMISSION = Permission(name="read", description="Read access")
WRITE_PERMISSION = Permission(name="write", description="Write access")
DELETE_PERMISSION = Permission(name="delete", description="Delete access")

DEVICE_PERMISSIONS = Permission(
    name="device",
    description="Access to devices",
    sub_permissions=[READ_PERMISSION, WRITE_PERMISSION, DELETE_PERMISSION],
)
SOFTWARE_PERMISSIONS = Permission(
    name="software",
    description="Access to software",
    sub_permissions=[READ_PERMISSION, WRITE_PERMISSION, DELETE_PERMISSION],
)
ROLLOUT_PERMISSIONS = Permission(
    name="rollout",
    description="Access to rollouts",
    sub_permissions=[READ_PERMISSION, WRITE_PERMISSION, DELETE_PERMISSION],
)

API_PERMISSIONS = Permission(
    name="api",
    description="Access to the GooseBit API",
    sub_permissions=[DEVICE_PERMISSIONS, SOFTWARE_PERMISSIONS, ROLLOUT_PERMISSIONS],
)
UI_PERMISSIONS = Permission(
    name="ui",
    description="Access to the GooseBit UI",
    sub_permissions=[DEVICE_PERMISSIONS, SOFTWARE_PERMISSIONS, ROLLOUT_PERMISSIONS],
)

GOOSEBIT_PERMISSIONS = Permission(
    name="goosebit", description="Access to GooseBit", sub_permissions=[API_PERMISSIONS, UI_PERMISSIONS]
)
