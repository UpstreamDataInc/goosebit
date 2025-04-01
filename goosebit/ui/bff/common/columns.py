from .responses import DTColumnDescription


class DeviceColumns:
    id = DTColumnDescription(title="ID", data="id", name="id", searchable=True, orderable=True)
    name = DTColumnDescription(title="Name", data="name", name="name", searchable=True, orderable=True)
    hw_model = DTColumnDescription(title="Model", data="hw_model")
    hw_revision = DTColumnDescription(title="Revision", data="hw_revision")
    feed = DTColumnDescription(title="Feed", data="feed", name="feed", searchable=True, orderable=True)
    sw_version = DTColumnDescription(
        title="Installed Software", data="sw_version", name="sw_version", searchable=True, orderable=True
    )
    sw_target_version = DTColumnDescription(title="Target Software", data="sw_target_version")
    update_mode = DTColumnDescription(
        title="Update Mode", data="update_mode", name="update_mode", searchable=True, orderable=True
    )
    last_state = DTColumnDescription(
        title="State", data="last_state", name="last_state", searchable=True, orderable=True
    )
    force_update = DTColumnDescription(title="Force Update", data="force_update")
    progress = DTColumnDescription(title="Progress", data="progress")
    last_ip = DTColumnDescription(title="Last IP", data="last_ip")
    polling = DTColumnDescription(title="Polling", data="polling")
    last_seen = DTColumnDescription(title="Last Seen", data="last_seen")


class RolloutColumns:
    id = DTColumnDescription(title="ID", data="id", visible=False)
    created_at = DTColumnDescription(title="Created", data="created_at", name="created_at", orderable=True)
    name = DTColumnDescription(title="Name", data="name", name="name", searchable=True, orderable=True)
    feed = DTColumnDescription(title="Feed", data="feed", name="feed", searchable=True, orderable=True)
    sw_file = DTColumnDescription(title="Software File", data="sw_file", name="sw_file")
    sw_version = DTColumnDescription(title="Software Version", data="sw_version", name="sw_version")
    paused = DTColumnDescription(title="Paused", name="paused", data="paused")
    success_count = DTColumnDescription(title="Success Count", data="success_count", name="success_count")
    failure_count = DTColumnDescription(title="Failure Count", data="failure_count", name="failure_count")


class SoftwareColumns:
    id = DTColumnDescription(title="ID", data="id", visible=False)
    name = DTColumnDescription(title="Name", data="name", name="name")
    version = DTColumnDescription(title="Version", data="version", name="version", searchable=True, orderable=True)
    compatibility = DTColumnDescription(title="Compatibility", name="compatibility", data="compatibility")
    size = DTColumnDescription(title="Size", name="size", data="size")


class SettingsUsersColumns:
    username = DTColumnDescription(title="Username", data="username", searchable=True, orderable=True)
    enabled = DTColumnDescription(title="Enabled", data="enabled")
    permissions = DTColumnDescription(title="Permissions", data="permissions")
