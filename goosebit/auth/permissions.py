from typing import Optional

from pydantic import BaseModel, Field, computed_field


class Permission(BaseModel):
    def model_post_init(self, ctx):
        if self.sub_permissions is None:
            return
        for permission in self.sub_permissions:
            permission.parent_permission = self

    def __call__(self, *args, **kwargs) -> str:
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

    @computed_field  # type: ignore[misc]
    @property
    def value(self) -> str:
        return self()

    @computed_field  # type: ignore[misc]
    @property
    def parent(self) -> str | None:
        if self.parent_permission is not None:
            return self.parent_permission()
        return None

    name: str
    description: str

    parent_permission: Optional["Permission"] = Field(exclude=True, default=None)
    sub_permissions: list["Permission"] | None = None


READ_PERMISSION = Permission(name="read", description="Read access")
WRITE_PERMISSION = Permission(name="write", description="Write access")
DELETE_PERMISSION = Permission(name="delete", description="Delete access")

DEVICE_PERMISSIONS = Permission(
    name="device",
    description="Access to devices",
    sub_permissions=[READ_PERMISSION.model_copy(), WRITE_PERMISSION.model_copy(), DELETE_PERMISSION.model_copy()],
)
SOFTWARE_PERMISSIONS = Permission(
    name="software",
    description="Access to software",
    sub_permissions=[READ_PERMISSION.model_copy(), WRITE_PERMISSION.model_copy(), DELETE_PERMISSION.model_copy()],
)
ROLLOUT_PERMISSIONS = Permission(
    name="rollout",
    description="Access to rollouts",
    sub_permissions=[READ_PERMISSION.model_copy(), WRITE_PERMISSION.model_copy(), DELETE_PERMISSION.model_copy()],
)
SETTINGS_USERS_PERMISSIONS = Permission(
    name="users",
    description="Access to user control",
    sub_permissions=[READ_PERMISSION.model_copy(), WRITE_PERMISSION.model_copy(), DELETE_PERMISSION.model_copy()],
)
SETTING_PERMISSIONS = Permission(
    name="settings",
    description="Access to settings",
    sub_permissions=[SETTINGS_USERS_PERMISSIONS],
)

GOOSEBIT_PERMISSIONS = Permission(
    name="goosebit",
    description="Full access to GooseBit",
    sub_permissions=[DEVICE_PERMISSIONS, SOFTWARE_PERMISSIONS, ROLLOUT_PERMISSIONS, SETTING_PERMISSIONS],
)
