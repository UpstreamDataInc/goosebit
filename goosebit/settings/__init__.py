from .const import BASE_DIR, DB_MIGRATIONS_LOC, PWD_CXT, SECRET  # noqa: F401
from .schema import GooseBitSettings

config = GooseBitSettings()

ARTIFACTS_DIR = config.artifacts_dir
TENANT = config.tenant
POLL_TIME = config.poll_time_default
POLL_TIME_UPDATING = config.poll_time_updating
POLL_TIME_REGISTRATION = config.poll_time_registration
DB_URI = config.db_uri
USERS = {u.username: u for u in config.users}
LOGGING = config.logging

PROMETHEUS_PORT = config.metrics.prometheus.port
