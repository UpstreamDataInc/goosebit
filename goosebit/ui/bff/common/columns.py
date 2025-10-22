from .responses import DTColumnDescription


class DeviceColumns:
    id = DTColumnDescription(
        title="Device ID",
        data="id",
        name="id",
        searchable=True,
        orderable=True,
    )
    name = DTColumnDescription(
        title="Name",
        data="name",
        name="name",
        searchable=True,
        orderable=True,
    )
    hw_model = DTColumnDescription(
        title="Model",
        data="hardware.model",
        name="hardware__model",
        searchable=True,
        orderable=True,
    )
    hw_revision = DTColumnDescription(
        title="Revision",
        data="hardware.revision",
        name="hardware__revision",
        searchable=True,
        orderable=True,
    )
    feed = DTColumnDescription(
        title="Feed",
        data="feed",
        name="feed",
        searchable=True,
        orderable=True,
    )
    sw_version = DTColumnDescription(
        title="Installed Software",
        data="sw_version",
        name="sw_version",
        searchable=True,
        orderable=True,
    )
    sw_target_version = DTColumnDescription(
        title="Target Software",
        data="assigned_software.version",
        name="assigned_software__version",
        searchable=True,
        orderable=True,
    )
    update_mode = DTColumnDescription(
        title="Update Mode",
        data="update_mode",
        name="update_mode",
        orderable=True,
    )
    last_state = DTColumnDescription(
        title="State",
        data="last_state",
        name="last_state",
        orderable=True,
    )
    force_update = DTColumnDescription(
        title="Force Update",
        data="force_update",
        name="force_update",
        orderable=True,
    )
    progress = DTColumnDescription(
        title="Progress",
        data="progress",
        name="progress",
        orderable=True,
    )
    last_ip = DTColumnDescription(
        title="Last IP",
        data="last_ip",
        name="last_ip",
        searchable=True,
        orderable=True,
    )
    polling = DTColumnDescription(
        title="Polling",
        data="polling",
    )
    last_seen = DTColumnDescription(
        title="Last Seen",
        data="last_seen",
        name="last_seen",
        orderable=True,
    )


class RolloutColumns:
    id = DTColumnDescription(
        title="ID",
        data="id",
        visible=False,
    )
    created_at = DTColumnDescription(
        title="Created",
        data="created_at",
        name="created_at",
        orderable=True,
    )
    name = DTColumnDescription(
        title="Name",
        data="name",
        name="name",
        searchable=True,
        orderable=True,
    )
    feed = DTColumnDescription(
        title="Feed",
        data="feed",
        name="feed",
        searchable=True,
        orderable=True,
    )
    sw_file = DTColumnDescription(
        title="Software File",
        data="software.name",
        name="software__uri",  # May cause strange orderings sorting by uri instead of the end of the path
        searchable=True,
        orderable=True,
    )
    sw_version = DTColumnDescription(
        title="Software Version",
        data="software.version",
        name="software__version",
        searchable=True,
        orderable=True,
    )
    paused = DTColumnDescription(
        title="Paused",
        name="paused",
        data="paused",
        orderable=True,
    )
    success_count = DTColumnDescription(
        title="Success Count",
        data="success_count",
        name="success_count",
        orderable=True,
    )
    failure_count = DTColumnDescription(
        title="Failure Count",
        data="failure_count",
        name="failure_count",
        orderable=True,
    )


class SoftwareColumns:
    id = DTColumnDescription(
        title="ID",
        data="id",
        visible=False,
    )
    name = DTColumnDescription(
        title="Name",
        data="name",
        name="uri",  # May cause strange orderings sorting by uri instead of the end of the path
        searchable=True,
        orderable=True,
    )
    version = DTColumnDescription(
        title="Version",
        data="version",
        name="version",
        searchable=True,
        orderable=True,
    )
    compatibility = DTColumnDescription(
        title="Compatibility",
        name="compatibility",
        data="compatibility",
    )
    size = DTColumnDescription(
        title="Size",
        name="size",
        data="size",
        orderable=True,
    )


class SettingsUsersColumns:
    username = DTColumnDescription(
        title="Username",
        data="username",
        searchable=True,
        orderable=True,
    )
    enabled = DTColumnDescription(
        title="Enabled",
        data="enabled",
        orderable=True,
    )
    permissions = DTColumnDescription(
        title="Permissions",
        data="permissions",
    )
